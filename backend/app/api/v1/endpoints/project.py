"""Project endpoints: multi-step guided projects (18.8 / 19.6).

43.6 (ADR-65 D8): `submit-step` ya no se cree al cliente. El paso enviado tiene
que ser el actual; el código se guarda siempre; los pasos SQL los ejecuta el
servidor (`sql_sandbox`) y el `passed` del cliente se ignora; los de Python/JS
siguen en el navegador y su finalización queda sin verificar.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

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
    StepSubmitResult,
    SubmissionRead,
)
from app.services.sql_sandbox import check_sql_async

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


@router.post("/{slug}/submit-step", response_model=StepSubmitResult)
async def submit_step(
    slug: str,
    body: StepSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StepSubmitResult:
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
    if submission.completed:
        raise HTTPException(status.HTTP_409_CONFLICT, "already completed")
    if body.step_number != submission.current_step:
        raise HTTPException(status.HTTP_409_CONFLICT, "not the current step")
    step = next((s for s in project.steps if s.step_number == body.step_number), None)
    if step is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "step not found")

    # Se guarda también lo que no pasa: salir y volver no pierde el trabajo.
    submission.step_code = {**(submission.step_code or {}), str(step.step_number): body.code}

    error: str | None = None
    timed_out = False
    if project.runtime == "sql":
        check = await check_sql_async(body.code, step.test_code)
        passed, error, timed_out = check.passed, check.error, check.timed_out
    else:
        # Sin sandbox para Python/JS: el resultado es el del navegador, pero el
        # código de partida sin tocar no cuenta como paso hecho.
        passed = body.passed and body.code.strip() not in ("", step.starter_code.strip())

    if passed:
        last = max(s.step_number for s in project.steps)
        if step.step_number >= last:
            submission.completed = True
            submission.completed_at = datetime.now(UTC)
            submission.verified = project.runtime == "sql"
        else:
            submission.current_step = step.step_number + 1

    await db.commit()
    await db.refresh(submission)
    return StepSubmitResult(
        **SubmissionRead.model_validate(submission).model_dump(),
        step_passed=passed,
        error=error,
        timed_out=timed_out,
    )
