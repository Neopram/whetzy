"""Background job service for async task execution.

Series 22.6: Process queued jobs (email, exports, model training, etc.)
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy import and_, select
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


async def process_pending_jobs(db: AsyncSession, max_jobs: int = 10) -> int:
    """Poll for pending jobs and process them. Return count processed."""
    # Fetch up to max_jobs pending jobs
    jobs = (
        await db.scalars(
            select(Job)
            .where(Job.status == "queued")
            .order_by(Job.created_at)
            .limit(max_jobs)
        )
    ).all()

    if not jobs:
        return 0

    count = 0
    for job in jobs:
        try:
            job.status = "running"
            job.started_at = datetime.utcnow()
            await db.commit()

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


@register_job_handler("run_payouts")
async def handle_run_payouts(job: Job, db: AsyncSession) -> dict[str, Any]:
    """Handler for monthly payout processing (28.7).
    
    Process pending instructor payouts that meet the €50 minimum threshold.
    
    Returns:
        {
            "processed_count": int,           # Number of instructors paid
            "total_paid_cents": int,          # Total payout in cents
            "instructor_count": int,          # Count of instructors with pending payouts
            "filtered_out_count": int,        # Count under minimum threshold
        }
    """
    from app.models.instructor import InstructorPayout

    # Minimum payout threshold in cents: €50 = 5000 cents
    MIN_PAYOUT_CENTS = 5000

    logger.info("Executing monthly payout job")

    # 1. SELECT pending instructor payouts
    pending_payouts = (
        await db.scalars(
            select(InstructorPayout)
            .where(
                and_(
                    InstructorPayout.status == "pending",
                    InstructorPayout.earnings_cents > 0,
                )
            )
            .order_by(InstructorPayout.instructor_id)
        )
    ).all()

    if not pending_payouts:
        logger.info("No pending payouts to process")
        return {
            "processed_count": 0,
            "total_paid_cents": 0,
            "instructor_count": 0,
            "filtered_out_count": 0,
        }

    # 2. Filter: >= €50 minimum
    valid_payouts = [p for p in pending_payouts if p.earnings_cents >= MIN_PAYOUT_CENTS]
    filtered_out = len(pending_payouts) - len(valid_payouts)

    logger.info(
        "Processing payouts: %d valid (>= €50), %d filtered out",
        len(valid_payouts),
        filtered_out,
    )

    total_paid_cents = 0
    instructor_count = len(valid_payouts)

    # 3-4. Process each payout: update status to 'processing'
    for payout in valid_payouts:
        payout.status = "processing"
        total_paid_cents += payout.earnings_cents
        logger.debug(
            "Payout for instructor %s: €%.2f",
            payout.instructor_id,
            payout.earnings_cents / 100,
        )

    # Commit all status updates to 'processing'
    await db.commit()
    logger.info(
        "Processed %d payouts totaling €%.2f",
        len(valid_payouts),
        total_paid_cents / 100,
    )

    # 5. Return statistics
    return {
        "processed_count": len(valid_payouts),
        "total_paid_cents": total_paid_cents,
        "instructor_count": instructor_count,
        "filtered_out_count": filtered_out,
    }
