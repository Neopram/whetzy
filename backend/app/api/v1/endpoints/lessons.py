"""Lessons endpoints: instructional content per skill, public and read-only."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.content import Lesson, Skill
from app.schemas.content import LessonRead

router = APIRouter()


@router.get("/{skill_id}", response_model=list[LessonRead])
async def lessons_for_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[Lesson]:
    skill = await db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

    result = await db.execute(
        select(Lesson)
        .where(Lesson.skill_id == skill_id)
        .order_by(Lesson.order)
    )
    return list(result.scalars().all())
