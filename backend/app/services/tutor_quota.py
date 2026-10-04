"""Cupo diario del tutor (38.6, ADR-49).

Pro (`plus`) tiene `TUTOR_DAILY_LIMIT_PLUS` explicaciones por día UTC; Pro Max
(`pro`), Creador, el dueño y los admins no tienen cupo. El uso se cuenta en
todos los planes: sin esa cifra no hay forma de saber cuánto cuesta el tutor
ilimitado. El freno por minuto del middleware sigue aparte y vale para todos.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
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


async def _increment_if_exists(db: AsyncSession, user_id: uuid.UUID, day: date) -> int | None:
    """`UPDATE ... SET explanations = explanations + 1`, atómico en la base:
    no hay lectura en Python que una segunda llamada pueda pisar. None si
    la fila de hoy todavía no existe (no afectó ninguna)."""
    result = await db.execute(
        update(TutorUsage)
        .where(TutorUsage.user_id == user_id, TutorUsage.day == day)
        .values(explanations=TutorUsage.explanations + 1)
        .returning(TutorUsage.explanations)
    )
    row = result.first()
    return int(row[0]) if row is not None else None


async def record(db: AsyncSession, user_id: uuid.UUID, day: date) -> int:
    """S.17: lee-suma-escribe en Python era una carrera real -- dos llamadas
    a /tutor/explain a la vez (dos pestañas, o un script) podían leer la
    misma fila antes de que ninguna hiciera commit, y la que comiteara
    segunda pisaba el incremento de la primera: dos explicaciones servidas
    (y dos llamadas reales al LLM cobradas) contaban como una sola en el
    cupo, dejando pasar más peticiones de las que el plan Plus permite.

    `_increment_if_exists` es atómico; si la fila de hoy todavía no existe
    se crea con un `INSERT` protegido por savepoint, igual que
    `certification.grant`, para la misma carrera en la primera llamada del
    día entre dos usuarios -- un `UPDATE` que no afectó ninguna fila puede
    deberse a que otra petición ganó la carrera de crearla entre medias; se
    reintenta el incremento, que esta vez sí la encuentra.
    """
    updated = await _increment_if_exists(db, user_id, day)
    if updated is not None:
        return updated

    try:
        async with db.begin_nested():
            db.add(TutorUsage(user_id=user_id, day=day, explanations=1))
            await db.flush()
        return 1
    except IntegrityError:
        updated = await _increment_if_exists(db, user_id, day)
        if updated is None:
            raise
        return updated
