"""Cupo diario del tutor (38.6, ADR-49).

Pro (`plus`) tiene `TUTOR_DAILY_LIMIT_PLUS` explicaciones por día UTC; Pro Max
(`pro`), Creador, el dueño y los admins no tienen cupo. El uso se cuenta en
todos los planes: sin esa cifra no hay forma de saber cuánto cuesta el tutor
ilimitado. El freno por minuto del middleware sigue aparte y vale para todos.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.entitlements import user_meets_tier
from app.models.tutor_usage import TutorUsage
from app.models.user import User

LIMIT_REACHED = "tutor_daily_limit"


def today_utc(now: datetime | None = None) -> date:
    return (now or datetime.now(UTC)).astimezone(UTC).date()


def resets_at(day: date) -> datetime:
    return datetime.combine(day + timedelta(days=1), time.min, tzinfo=UTC)


def daily_limit(user: User) -> int | None:
    """Cupo del usuario, o None si no tiene."""
    if user.is_admin or user.role == "owner" or user_meets_tier(user, "pro"):
        return None
    return settings.TUTOR_DAILY_LIMIT_PLUS


async def used_on(db: AsyncSession, user_id: uuid.UUID, day: date) -> int:
    row = await db.get(TutorUsage, (user_id, day))
    return row.explanations if row else 0


async def record(db: AsyncSession, user_id: uuid.UUID, day: date) -> int:
    row = await db.get(TutorUsage, (user_id, day))
    if row is None:
        row = TutorUsage(user_id=user_id, day=day, explanations=0)
        db.add(row)
    row.explanations += 1
    await db.flush()
    return row.explanations
