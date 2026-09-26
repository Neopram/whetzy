"""Bootcamp endpoints: structured multi-week learning paths (19.4)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.bootcamp import Bootcamp, BootcampEnrollment
from app.models.user import User
from app.schemas.bootcamp import BootcampDetail, BootcampRead, EnrollmentRead

router = APIRouter()


@router.get("", response_model=list[BootcampRead])
async def list_bootcamps(db: AsyncSession = Depends(get_db)) -> list[Bootcamp]:
    result = await db.execute(select(Bootcamp).order_by(Bootcamp.order))
    return list(result.scalars().all())


@router.get("/{slug}", response_model=BootcampDetail)
async def get_bootcamp(slug: str, db: AsyncSession = Depends(get_db)) -> Bootcamp:
    result = await db.execute(
        select(Bootcamp)
        .where(Bootcamp.slug == slug)
        .options(selectinload(Bootcamp.weeks))
    )
    bootcamp = result.scalar_one_or_none()
    if bootcamp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "bootcamp not found")
    return bootcamp


@router.post("/{slug}/enroll", response_model=EnrollmentRead, status_code=201)
async def enroll_in_bootcamp(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BootcampEnrollment:
    result = await db.execute(select(Bootcamp).where(Bootcamp.slug == slug))
    bootcamp = result.scalar_one_or_none()
    if bootcamp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "bootcamp not found")

    existing = await db.execute(
        select(BootcampEnrollment).where(
            BootcampEnrollment.bootcamp_id == bootcamp.id,
            BootcampEnrollment.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "already enrolled")

    enrollment = BootcampEnrollment(
        id=uuid.uuid4(),
        bootcamp_id=bootcamp.id,
        user_id=current_user.id,
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


@router.get("/{slug}/progress", response_model=EnrollmentRead)
async def get_bootcamp_progress(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BootcampEnrollment:
    result = await db.execute(select(Bootcamp).where(Bootcamp.slug == slug))
    bootcamp = result.scalar_one_or_none()
    if bootcamp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "bootcamp not found")

    enrollment = await db.execute(
        select(BootcampEnrollment).where(
            BootcampEnrollment.bootcamp_id == bootcamp.id,
            BootcampEnrollment.user_id == current_user.id,
        )
    )
    result_row = enrollment.scalar_one_or_none()
    if result_row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not enrolled")
    return result_row
