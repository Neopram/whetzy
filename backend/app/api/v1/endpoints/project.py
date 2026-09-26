"""Project endpoints: multi-step guided projects with browser-side tests (18.8 / 19.6)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.project import Project, ProjectSubmission
from app.models.user import User
from app.schemas.project import (
    ProjectDetail,
    ProjectRead,
    StepSubmitRequest,
    SubmissionRead,
)

router = APIRouter()


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    track_id: str | None = None,
    runtime: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[Project]:
    stmt = select(Project).order_by(Project.order)
    if track_id:
        stmt = stmt.where(Project.track_id == track_id)
    if runtime:
        stmt = stmt.where(Project.runtime == runtime)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{slug}", response_model=ProjectDetail)
async def get_project(slug: str, db: AsyncSession = Depends(get_db)) -> Project:
    result = await db.execute(
        select(Project)
        .where(Project.slug == slug)
        .options(selectinload(Project.steps))
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")
    return project


@router.post("/{slug}/start", response_model=SubmissionRead, status_code=201)
async def start_project(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectSubmission:
    result = await db.execute(select(Project).where(Project.slug == slug))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")

    existing = await db.execute(
        select(ProjectSubmission).where(
            ProjectSubmission.project_id == project.id,
            ProjectSubmission.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "already started")

    submission = ProjectSubmission(
        id=uuid.uuid4(),
        project_id=project.id,
        user_id=current_user.id,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


@router.get("/{slug}/progress", response_model=SubmissionRead)
async def get_project_progress(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectSubmission:
    result = await db.execute(select(Project).where(Project.slug == slug))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")

    sub = await db.execute(
        select(ProjectSubmission).where(
            ProjectSubmission.project_id == project.id,
            ProjectSubmission.user_id == current_user.id,
        )
    )
    submission = sub.scalar_one_or_none()
    if submission is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not started")
    return submission


@router.post("/{slug}/submit-step", response_model=SubmissionRead)
async def submit_step(
    slug: str,
    body: StepSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectSubmission:
    result = await db.execute(
        select(Project)
        .where(Project.slug == slug)
        .options(selectinload(Project.steps))
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")

    sub = await db.execute(
        select(ProjectSubmission).where(
            ProjectSubmission.project_id == project.id,
            ProjectSubmission.user_id == current_user.id,
        )
    )
    submission = sub.scalar_one_or_none()
    if submission is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not started")

    if not body.passed:
        return submission

    total_steps = len(project.steps)
    if body.step_number >= total_steps:
        submission.completed = True
        from sqlalchemy.sql import func
        submission.completed_at = func.now()
    else:
        submission.current_step = body.step_number + 1

    await db.commit()
    await db.refresh(submission)
    return submission
