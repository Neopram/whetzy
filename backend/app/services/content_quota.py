"""Cupo diario de contenido del plan Free (39.4, ADR-50a).

Free tiene `FREE_DAILY_NEW_QUESTIONS` preguntas **nuevas** y `FREE_DAILY_LESSONS`
lecciones al día UTC. Una pregunta es nueva si el usuario no la había respondido
nunca antes de hoy; solo cuenta la que se responde en modo `study`. Quedan fuera
los repasos FSRS (`review`), el placement y los exámenes: el repaso espaciado es
el motor del producto y es gratis para todos (ver `quiz.py`).

Todo va detrás de `FREE_DAILY_QUOTA_ENABLED`, apagado hasta que abra el cobro
(H.19/H.29): limitar para empujar a un plan que nadie puede comprar cierra el
producto. Pro, Pro Max, Creador, el dueño y los admins no tienen cupo.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.entitlements import user_meets_tier
from app.models.lesson_view import LessonView
from app.models.session import Response, StudySession
from app.models.user import User

QUOTA_REACHED = "free_daily_quota"
# Modos que nunca gastan cupo ni se bloquean.
EXEMPT_MODES = frozenset({"review", "placement", "exam"})


def today_utc(now: datetime | None = None) -> date:
    return (now or datetime.now(UTC)).astimezone(UTC).date()


def _day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=UTC)
    return start, start + timedelta(days=1)


def applies_to(user: User) -> bool:
    """True si el cupo Free se aplica a este usuario ahora mismo."""
    if not settings.FREE_DAILY_QUOTA_ENABLED:
        return False
    if user.is_admin or user.role == "owner":
        return False
    return not user_meets_tier(user, "plus")


def quota_detail(kind: str, limit: int, day: date) -> dict[str, Any]:
    return {
        "code": QUOTA_REACHED,
        "kind": kind,
        "limit": limit,
        "resets_at": _day_bounds(day)[1].isoformat(),
    }


async def new_questions_on(db: AsyncSession, user_id: uuid.UUID, day: date) -> int:
    """Preguntas respondidas en modo `study` ese día que el usuario no había visto antes."""
    start, end = _day_bounds(day)
    today = set(
        (
            await db.execute(
                select(Response.question_id)
                .join(StudySession, Response.session_id == StudySession.id)
                .where(
                    StudySession.user_id == user_id,
                    StudySession.mode == "study",
                    Response.created_at >= start,
                    Response.created_at < end,
                )
            )
        ).scalars()
    )
    if not today:
        return 0
    before = set(
        (
            await db.execute(
                select(Response.question_id)
                .join(StudySession, Response.session_id == StudySession.id)
                .where(
                    StudySession.user_id == user_id,
                    Response.created_at < start,
                    Response.question_id.in_(today),
                )
            )
        ).scalars()
    )
    return len(today - before)


async def new_questions_left(db: AsyncSession, user: User, mode: str) -> int | None:
    """Preguntas nuevas que le quedan hoy, o None si el cupo no aplica."""
    if mode in EXEMPT_MODES or not applies_to(user):
        return None
    used = await new_questions_on(db, user.id, today_utc())
    return max(0, settings.FREE_DAILY_NEW_QUESTIONS - used)


async def enforce_new_questions(db: AsyncSession, user: User, mode: str) -> None:
    """429 si el usuario Free ya gastó hoy sus preguntas nuevas."""
    left = await new_questions_left(db, user, mode)
    if left == 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=quota_detail("questions", settings.FREE_DAILY_NEW_QUESTIONS, today_utc()),
        )


async def enforce_and_record_lesson(db: AsyncSession, user: User, skill_id: str) -> None:
    """Cuenta la lección de `skill_id` para hoy; 429 si sería la sexta distinta.

    Volver a abrir una lección ya abierta hoy no gasta cupo.
    """
    if not applies_to(user):
        return
    day = today_utc()
    seen = set(
        (
            await db.execute(
                select(LessonView.skill_id).where(
                    LessonView.user_id == user.id, LessonView.day == day
                )
            )
        ).scalars()
    )
    if skill_id in seen:
        return
    if len(seen) >= settings.FREE_DAILY_LESSONS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=quota_detail("lessons", settings.FREE_DAILY_LESSONS, day),
        )
    db.add(LessonView(user_id=user.id, skill_id=skill_id, day=day))
    await db.commit()
