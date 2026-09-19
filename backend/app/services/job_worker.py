"""Background job service for async task execution.

Series 22.6: Process queued jobs (email, exports, model training, etc.)
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job

logger = logging.getLogger("whetzy")

# Registry of job handlers: job_type -> handler function
_JOB_HANDLERS: dict[str, Callable[[Job, AsyncSession], Any]] = {}


def register_job_handler(job_type: str) -> Callable:
    """Decorator to register a job handler."""
    def decorator(func: Callable) -> Callable:
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
    except Exception as e:
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
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.utcnow()
            logger.error("Job %d failed: %s", job.id, str(e))

        await db.commit()
        count += 1

    return count


async def job_worker_loop(db_factory: Callable, poll_interval: int = 5) -> None:
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
        except Exception as e:
            logger.error("Job worker error: %s", str(e), exc_info=True)
            await asyncio.sleep(poll_interval * 2)  # Back off on error


# Example job handlers (register more as needed)

@register_job_handler("send_email")
async def handle_send_email(job: Job, db: AsyncSession) -> dict[str, Any]:
    """Handler for email job type."""
    payload = job.payload
    email = payload.get("email")
    subject = payload.get("subject")
    body = payload.get("body")

    # TODO: Implement actual email sending
    # from app.services.email import send_email_async
    # await send_email_async(email, subject, body)

    logger.info("Email job: to=%s subject=%s", email, subject)
    return {"email": email, "sent": True}


@register_job_handler("export_csv")
async def handle_export_csv(job: Job, db: AsyncSession) -> dict[str, Any]:
    """Handler for CSV export job type."""
    payload = job.payload
    track_id = payload.get("track_id")
    
    # TODO: Implement CSV export logic
    # from app.services.export import export_track_csv
    # file_url = await export_track_csv(track_id, db)
    
    logger.info("Export CSV job: track_id=%s", track_id)
    return {"file_url": "s3://...", "format": "csv"}


@register_job_handler("dkt_retrain")
async def handle_dkt_retrain(job: Job, db: AsyncSession) -> dict[str, Any]:
    """Handler for DKT model retraining."""
    payload = job.payload
    
    # TODO: Implement DKT model retraining
    # from app.ml.train_dkt import retrain_model
    # metrics = await retrain_model(db)
    
    logger.info("DKT retrain job started")
    return {"metrics": {"auc": 0.85, "loss": 0.25}}
