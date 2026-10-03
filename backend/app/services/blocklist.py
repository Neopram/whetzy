"""Consultas de bloqueo entre usuarios para duels.py y social.py (19.11)."""

from __future__ import annotations

import uuid

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.moderation import UserBlock


async def is_blocked_pair(db: AsyncSession, user_a: uuid.UUID, user_b: uuid.UUID) -> bool:
    """True si cualquiera de los dos bloqueó al otro."""
    result = await db.execute(
        select(UserBlock.id)
        .where(
            or_(
                and_(UserBlock.blocker_id == user_a, UserBlock.blocked_id == user_b),
                and_(UserBlock.blocker_id == user_b, UserBlock.blocked_id == user_a),
            )
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def blocked_user_ids(db: AsyncSession, user_id: uuid.UUID) -> set[uuid.UUID]:
    """Todos los usuarios que bloquean a `user_id` o a quienes `user_id` bloquea."""
    result = await db.execute(
        select(UserBlock.blocker_id, UserBlock.blocked_id).where(
            or_(UserBlock.blocker_id == user_id, UserBlock.blocked_id == user_id)
        )
    )
    ids: set[uuid.UUID] = set()
    for blocker_id, blocked_id in result.all():
        ids.add(blocker_id if blocker_id != user_id else blocked_id)
    return ids
