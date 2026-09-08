"""ML management endpoints — model registry info and rollback."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.ml.registry import registry
from app.models.session import StudySession
from app.models.user import User

router = APIRouter()


@router.get("/version", summary="Active DKT checkpoint version")
async def get_ml_version(
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Return info about the currently loaded DKT model checkpoint."""
    return registry.current_info()


@router.get("/ab-stats", summary="A/B experiment: BKT vs DKT skill-selection cohort stats")
async def get_ab_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Per-cohort user counts and quiz performance metrics.

    Assignment is deterministic (hash of user_id), so no DB column is needed.
    """
    from app.services.ab_harness import get_cohort

    user_rows = await db.execute(select(User.id))
    cohort_map: dict[str, str] = {str(uid): get_cohort(uid) for (uid,) in user_rows.all()}

    sess_rows = await db.execute(
        select(
            StudySession.user_id,
            func.count(StudySession.id).label("sessions"),
            func.sum(StudySession.questions_answered).label("questions"),
            func.sum(StudySession.correct_count).label("correct"),
        )
        .where(StudySession.ended_at.is_not(None))
        .group_by(StudySession.user_id)
    )

    totals: dict[str, dict[str, int]] = {
        "bkt": {"users": 0, "sessions": 0, "questions": 0, "correct": 0},
        "dkt": {"users": 0, "sessions": 0, "questions": 0, "correct": 0},
    }
    for cohort in totals:
        totals[cohort]["users"] = sum(1 for c in cohort_map.values() if c == cohort)

    for row in sess_rows.all():
        cohort = cohort_map.get(str(row.user_id), "bkt")
        totals[cohort]["sessions"] += int(row.sessions or 0)
        totals[cohort]["questions"] += int(row.questions or 0)
        totals[cohort]["correct"] += int(row.correct or 0)

    result: dict[str, Any] = {}
    for cohort, s in totals.items():
        q = s["questions"]
        result[cohort] = {
            "users": s["users"],
            "sessions": s["sessions"],
            "questions_answered": q,
            "accuracy": round(s["correct"] / q, 4) if q > 0 else None,
        }
    return result


@router.post("/rollback", summary="Roll back to a previous DKT checkpoint")
async def rollback_model(
    version: int,
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Load a specific DKT checkpoint version (replaces the active model)."""
    available = registry.list_versions()
    if not available:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No DKT checkpoints found.",
        )
    if version not in available:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version v{version} not found. Available: {available}",
        )
    await registry.rollback(version)
    return registry.current_info()
