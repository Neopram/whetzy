"""Reportar y bloquear a otro usuario (19.11, App Store 1.2/1.2.1).

Mínimo a propósito: un reporte es un registro para que el dueño lo revise,
sin cola ni acción automática. Un bloqueo es bidireccional para quien lo
sufre — `duels.py` y `social.py` lo consultan para no volver a emparejar ni
mostrar a ninguna de las dos partes en las ligas del otro.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.moderation import UserBlock, UserReport
from app.models.user import User
from app.schemas.moderation import (
    BlockedUserRead,
    UserBlockRequest,
    UserReportRead,
    UserReportRequest,
)

router = APIRouter()


@router.post("/report", response_model=UserReportRead, status_code=status.HTTP_201_CREATED)
async def report_user(
    payload: UserReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserReport:
    if payload.reported_user_id == current_user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't report yourself")

    exists = await db.execute(select(User.id).where(User.id == payload.reported_user_id))
    if exists.scalar_one_or_none() is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    report = UserReport(
        reporter_id=current_user.id,
        reported_id=payload.reported_user_id,
        reason=payload.reason,
        context=payload.context,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.post("/block", response_model=BlockedUserRead, status_code=status.HTTP_201_CREATED)
async def block_user(
    payload: UserBlockRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BlockedUserRead:
    if payload.user_id == current_user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't block yourself")

    target = await db.execute(select(User).where(User.id == payload.user_id))
    blocked_user = target.scalar_one_or_none()
    if blocked_user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    existing = await db.execute(
        select(UserBlock).where(
            UserBlock.blocker_id == current_user.id, UserBlock.blocked_id == payload.user_id
        )
    )
    block = existing.scalar_one_or_none()
    if block is None:
        block = UserBlock(blocker_id=current_user.id, blocked_id=payload.user_id)
        db.add(block)
        await db.commit()
        await db.refresh(block)

    return BlockedUserRead(
        user_id=blocked_user.id,
        username=blocked_user.username,
        display_name=blocked_user.display_name,
        blocked_at=block.created_at,
    )


@router.delete("/block/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unblock_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await db.execute(
        delete(UserBlock).where(UserBlock.blocker_id == current_user.id, UserBlock.blocked_id == user_id)
    )
    await db.commit()


@router.get("/blocked", response_model=list[BlockedUserRead])
async def list_blocked(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BlockedUserRead]:
    rows = await db.execute(
        select(UserBlock, User)
        .join(User, User.id == UserBlock.blocked_id)
        .where(UserBlock.blocker_id == current_user.id)
        .order_by(UserBlock.created_at.desc())
    )
    return [
        BlockedUserRead(
            user_id=user.id, username=user.username, display_name=user.display_name,
            blocked_at=block.created_at,
        )
        for block, user in rows.all()
    ]
