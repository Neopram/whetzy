"""Background job service for async task execution.

Series 22.6: Process queued jobs (email, exports, model training, etc.)
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job

logger = logging.getLogger("whetzy")

# Registry of job handlers: job_type -> handler function
_JOB_HANDLERS: dict[str, Callable[[Job, AsyncSession], Any]] = {}


def register_job_handler(job_type: str) -> Callable[..., Any]:
    """Decorator to register a job handler."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        _JOB_HANDLERS[job_type] = func
        logger.info("Registered job handler: %s", job_type)
        return func
    return decorator


async def execute_job(job: Job, db: AsyncSession) -> dict[str, Any]:
    """Execute a single job. Update job status in DB."""
    handler = _JOB_HANDLERS.get(job.job_type)
    if not handler:
        raise ValueError(f"No handler for job type: {job.job_type}")

    try:
        result = await handler(job, db)
        return result or {}
    except Exception:
        logger.exception("Job %d (%s) failed", job.id, job.job_type)
        raise


def claim_query(max_jobs: int) -> Select[Job]:
    """Los `max_jobs` trabajos en cola más antiguos, bloqueados para este worker.

    `FOR UPDATE SKIP LOCKED`: con `--workers 2` en `start.sh` hay dos bucles
    `job_worker_loop`, uno por proceso, y sin bloqueo los dos leían la misma
    cola y ejecutaban cada trabajo dos veces (`run_payouts` es una liquidación
    a instructores). Con `SKIP LOCKED` el segundo salta las filas que el
    primero ya tiene y no espera. SQLite no tiene `FOR UPDATE` y lo omite.
    """
    return (
        select(Job)
        .where(Job.status == "queued")
        .order_by(Job.created_at, Job.id)
        .limit(max_jobs)
        .with_for_update(skip_locked=True)
    )


async def claim_pending_jobs(db: AsyncSession, max_jobs: int = 10) -> list[Job]:
    """Reclama un lote: lo marca `running` en la misma transacción que lo bloquea.

    Marcarlos de uno en uno (como antes) soltaba el bloqueo de todo el lote en
    el primer `commit`, y el resto volvía a quedar a la vista de otro worker.
    """
    jobs = list((await db.scalars(claim_query(max_jobs))).all())
    now = datetime.utcnow()
    for job in jobs:
        job.status = "running"
        job.started_at = now
    await db.commit()
    return jobs


async def process_pending_jobs(db: AsyncSession, max_jobs: int = 10) -> int:
    """Reclama trabajos en cola y los ejecuta. Devuelve cuántos procesó."""
    jobs = await claim_pending_jobs(db, max_jobs)
    if not jobs:
        return 0

    count = 0
    for job in jobs:
        try:
            result = await execute_job(job, db)

            job.status = "done"
            job.result = result
            job.completed_at = datetime.utcnow()
            logger.info("Job %d completed: %s", job.id, job.job_type)
        except Exception as e:  # un job roto no puede tumbar el worker
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.utcnow()
            logger.exception("Job %d failed", job.id)

        await db.commit()
        count += 1

    return count


async def job_worker_loop(db_factory: Callable[..., Any], poll_interval: int = 5) -> None:
    """Background worker: poll for jobs and execute them.
    
    Run this in app lifespan:
        job_worker_task = asyncio.create_task(job_worker_loop(AsyncSessionLocal))
    """
    logger.info("Job worker started (poll interval: %ds)", poll_interval)
    
    while True:
        try:
            async with db_factory() as db:
                await process_pending_jobs(db)
            await asyncio.sleep(poll_interval)
        except asyncio.CancelledError:
            logger.info("Job worker shutting down")
            break
        except Exception:  # el bucle del worker sobrevive a cualquier error
            logger.exception("Job worker error")
            await asyncio.sleep(poll_interval * 2)  # Back off on error


# Example job handlers (register more as needed)

@register_job_handler("send_email")
async def handle_send_email(job: Job, db: AsyncSession) -> dict[str, Any]:
    """Handler for email job type."""
    # Sin implementar: devolver {"sent": True} marcaria el job como hecho sin
    # haber enviado nada, y eso es exactamente la clase de mentira que prohibe
    # la linea roja 1. Falla, y `process_pending_jobs` lo deja en `failed`.
    raise NotImplementedError(
        "handler 'send_email' sin implementar (22.6): falta conectar app.services.email"
    )


@register_job_handler("export_csv")
async def handle_export_csv(job: Job, db: AsyncSession) -> dict[str, Any]:
    """Handler for CSV export job type."""
    raise NotImplementedError(
        "handler 'export_csv' sin implementar (22.6): falta app.services.export"
    )


@register_job_handler("dkt_retrain")
async def handle_dkt_retrain(job: Job, db: AsyncSession) -> dict[str, Any]:
    """Handler for DKT model retraining."""
    raise NotImplementedError(
        "handler 'dkt_retrain' sin implementar (22.6): falta app.ml.train_dkt"
    )


@register_job_handler("reactivation_check")
async def handle_reactivation_check(job: Job, db: AsyncSession) -> dict[str, Any]:
    """Encolable a mano; lo normal es `periodic_jobs_loop` (services/periodic.py)."""
    from app.services.periodic import send_reactivation_offers

    sent = await send_reactivation_offers(db)
    await db.commit()
    return {"sent": sent}


@register_job_handler("run_payouts")
async def handle_run_payouts(job: Job, db: AsyncSession) -> dict[str, Any]:
    """Liquidación (28.7), encolable a mano para cualquier día; lo normal es
    el día 15 desde `periodic_jobs_loop`."""
    from app.services.periodic import PAYOUT_DAY, process_monthly_payouts

    today = datetime.now(UTC)
    result = await process_monthly_payouts(db, now=today.replace(day=PAYOUT_DAY))
    await db.commit()
    return {**result, "instructor_count": result["processed_count"]}
