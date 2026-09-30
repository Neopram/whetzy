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
from app.services import content_quota, lesson_gate

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
        # 32.4: el rastro de "ya la vio" para el bloqueo del quiz es aparte del
        # cupo -- se registra siempre que haya sesión, aplique o no el cupo.
        await lesson_gate.record_lesson_seen(db, user.id, skill_id)

    if user is not None:
        # Con sesión la respuesta tiene efectos (cupo y rastro del bloqueo): si
        # el navegador la sirviera de su caché, la visita no llegaría aquí y
        # el quiz seguiría bloqueado (2026-09-30).
        response.headers["Cache-Control"] = "private, no-store"
    else:
        response.headers["Cache-Control"] = "public, max-age=7200, stale-while-revalidate=86400"
        # La sesión va en cookie (o Bearer): sin esto, una copia anónima cacheada se
        # reutilizaría ya con sesión y la visita tampoco llegaría aquí.
        response.headers["Vary"] = "Authorization, Cookie"
    result = await db.execute(
        select(Lesson)
        .where(Lesson.skill_id == skill_id)
        .order_by(Lesson.order)
    )
    return list(result.scalars().all())
