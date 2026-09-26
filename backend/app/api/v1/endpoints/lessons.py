"""Lessons endpoints: instructional content per skill, public and read-only."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_optional_user
from app.models.content import Lesson, Skill
from app.models.user import User
from app.schemas.content import LessonRead
from app.services import content_quota

router = APIRouter()


@router.get("/{skill_id}", response_model=list[LessonRead])
async def lessons_for_skill(
    skill_id: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> list[Lesson]:
    skill = await db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    # Cupo Free (39.4): solo cuenta con sesión y con el flag encendido. Sin sesión
    # la lección sigue siendo pública (ADR-50a, decisión anotada en DECISIONS.md).
    if user is not None:
        await content_quota.enforce_and_record_lesson(db, user, skill_id)

    response.headers["Cache-Control"] = "public, max-age=7200, stale-while-revalidate=86400"
    result = await db.execute(
        select(Lesson)
        .where(Lesson.skill_id == skill_id)
        .order_by(Lesson.order)
    )
    return list(result.scalars().all())
