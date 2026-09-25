"""FastAPI application entry point."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.db import close_db, get_db, init_db
from app.core.error_tracking import configure_sentry
from app.core.logging import RequestIDMiddleware, configure_logging
from app.core.metrics import MetricsMiddleware, metrics_endpoint
from app.core.security_middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from app.core.telemetry import configure_telemetry

configure_logging(level=logging.DEBUG if settings.DEBUG else logging.INFO)
configure_telemetry(settings.OTEL_SERVICE_NAME, settings.OTEL_EXPORTER_OTLP_ENDPOINT)
configure_sentry(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
)
logger = logging.getLogger("whetzy")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    import asyncio

    logger.info("Starting %s (env=%s, debug=%s)", settings.APP_NAME, settings.ENVIRONMENT, settings.DEBUG)
    if settings.ENVIRONMENT == "development":
        await init_db()
        logger.info("Development mode: ensured all tables exist")

    from app.core.db import AsyncSessionLocal
    from app.ml.registry import registry
    from app.services import email as email_svc
    from app.services.ai import rag
    from app.services.job_worker import job_worker_loop

    # Si el correo no sale, que se sepa al arrancar y no cuando alguien pierda
    # su cuenta. En produccion es un error, no un aviso (ledger H.30).
    _correo = email_svc.describe_config()
    if _correo["configured"]:
        logger.info("Email: proveedor %s, remitente %s", _correo["provider"], _correo["from"])
    elif settings.ENVIRONMENT == "production":
        logger.error(
            "email_not_configured — verificacion de cuenta y reset de contrasena NO "
            "se envian; se escriben en el log y se pierden. Define RESEND_API_KEY "
            "(o SMTP_USER y SMTP_PASSWORD). Ledger H.30"
        )
    else:
        logger.info("Email: sin proveedor, los mensajes van al log (entorno %s)", settings.ENVIRONMENT)

    asyncio.create_task(rag.build_bg(AsyncSessionLocal))
    logger.info("RAG: background index build scheduled")
    asyncio.create_task(registry.load())
    logger.info("DKT registry: background model load scheduled")
    asyncio.create_task(job_worker_loop(AsyncSessionLocal))
    logger.info("Job worker: background poll loop started")

    # Schedule monthly payouts (15th of each month at 00:00 UTC)
    _schedule_monthly_payouts(AsyncSessionLocal)
    logger.info("Monthly payout scheduler: scheduled for 15th of each month")

    yield
    logger.info("Shutting down %s", settings.APP_NAME)
    await close_db()


def _schedule_monthly_payouts(
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Schedule monthly payout job using APScheduler.
    
    Triggers on the 15th of each month at 00:00 UTC.
    """
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        async def _run_payout_job() -> None:
            """Create and queue a run_payouts job."""
            from uuid import uuid4

            from app.models.job import Job

            async with db_factory() as db:
                # Create a system job (user_id is a sentinel for scheduled jobs)
                job = Job(
                    user_id=uuid4(),
                    job_type="run_payouts",
                    status="queued",
                    payload={},
                )
                db.add(job)
                await db.commit()
                logger.info("Queued monthly payout job: %d", job.id)

        scheduler = AsyncIOScheduler()
        # Trigger at 00:00 UTC on the 15th of each month
        scheduler.add_job(
            _run_payout_job,
            trigger=CronTrigger(day=15, hour=0, minute=0, timezone="UTC"),
            id="monthly_payouts",
            name="Monthly instructor payouts",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("APScheduler started with monthly payout trigger")
    except ImportError:
        logger.warning("APScheduler not installed; monthly payouts will not be automatically scheduled")
    except Exception:
        logger.exception("Failed to configure monthly payout scheduler")


app = FastAPI(
    title=settings.APP_NAME,
    description="Adaptive learning platform backend — Python to AI Engineering.",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.active_cors_origins,  # 22.2: sin loopback en produccion
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus RED metrics (outermost so it captures total latency).
if settings.METRICS_ENABLED:
    app.add_middleware(MetricsMiddleware)

# ASVS 5.0 (L2): per-IP anti-automation + hardened security response headers.
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    default_limit=settings.DEFAULT_RATE_LIMIT,
    auth_limit=settings.AUTH_RATE_LIMIT,
)
app.add_middleware(
    SecurityHeadersMiddleware,
    enable_hsts=settings.ENVIRONMENT != "development",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Never echo the request body — it may contain passwords or PII (ASVS V7.1).
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    return {"name": settings.APP_NAME, "status": "ok", "version": "1.0.0"}


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/health/live", tags=["health"])
async def health_live() -> dict[str, str]:
    """Liveness probe — returns 200 as long as the process is running."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def health_ready(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Readiness probe — verifies the DB connection before accepting traffic."""
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not ready",
        ) from exc
    return {"status": "ready"}


app.add_route("/metrics", metrics_endpoint, include_in_schema=False)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
# Force redeploy
