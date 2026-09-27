"""Bloqueo del quiz hasta ver la lección del skill (32.4, decisión del dueño 2026-09-27).

Independiente del cupo Free (`content_quota.py`): se registra siempre que
haya sesión, sin mirar `FREE_DAILY_QUOTA_ENABLED` ni el tier del usuario --
gatear el quiz y limitar el cupo son dos reglas de negocio distintas que
comparten el mismo evento (abrir una lección) pero no la misma tabla.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson_completion import LessonCompletion


async def record_lesson_seen(db: AsyncSession, user_id: uuid.UUID, skill_id: str) -> None:
    """Idempotente: reabrir una lección ya vista no hace nada."""
    try:
        async with db.begin_nested():
            db.add(LessonCompletion(user_id=user_id, skill_id=skill_id))
            await db.flush()
    except IntegrityError:
        return
    await db.commit()


async def viewed_skill_ids(db: AsyncSession, user_id: uuid.UUID, skill_ids: list[str]) -> set[str]:
    """De `skill_ids`, los que el usuario ya abrió alguna vez -- 32.4."""
    if not skill_ids:
        return set()
    result = await db.execute(
        select(LessonCompletion.skill_id).where(
            LessonCompletion.user_id == user_id, LessonCompletion.skill_id.in_(skill_ids)
        )
    )
    return set(result.scalars())
