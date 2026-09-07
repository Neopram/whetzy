"""FastAPI application entry point."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.db import close_db, init_db
from app.core.security_middleware import RateLimitMiddleware, SecurityHeadersMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("whetzy")
logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    import asyncio

    logger.info("Starting %s (env=%s, debug=%s)", settings.APP_NAME, settings.ENVIRONMENT, settings.DEBUG)
    if settings.ENVIRONMENT == "development":
        await init_db()
        logger.info("Development mode: ensured all tables exist")

    from app.core.db import AsyncSessionLocal
    from app.services.ai import rag

    asyncio.create_task(rag.build_bg(AsyncSessionLocal))
    logger.info("RAG: background index build scheduled")

    yield
    logger.info("Shutting down %s", settings.APP_NAME)
    await close_db()


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
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ASVS 5.0 (L2): per-IP anti-automation + hardened security response headers.
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    SecurityHeadersMiddleware,
    enable_hsts=settings.ENVIRONMENT != "development",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    body = exc.body
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": body},
    )


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    return {"name": settings.APP_NAME, "status": "ok", "version": "1.0.0"}


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "healthy"}


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
