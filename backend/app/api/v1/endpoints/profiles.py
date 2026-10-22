"""Perfil público de un alumno por `username` (0.3).

Antes, la pantalla de perfil público del frontend mostraba datos
100% inventados ("Carlos Pérez", certificados y Elo de ejemplo) para
cualquier `username` -- nunca llamaba a ningún endpoint. Este es real o 404:
sin columna de privacidad todavía (otra migración; la 54 -- S.4 -- no está
en master, una a la vez), cualquier `username` existente y activo es
visible, igual que ya lo es un certificado por su código
(`GET /exams/certificates/{code}`), también sin autenticación.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.models.content import Track
from app.models.exam import Certificate
from app.models.project import Project, ProjectSubmission
from app.models.user import User, UserSkillState
from app.schemas.profile import (
    PublicCertificateRead,
    PublicProfileRead,
    PublicProjectRead,
)
from app.services.engine.domain_thresholds import mastered_clause

router = APIRouter()


@router.get("/{username}", response_model=PublicProfileRead)
async def get_public_profile(
    username: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> PublicProfileRead:
    if not settings.PUBLIC_PROFILES_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    user = (
        await db.scalars(select(User).where(User.username == username, User.is_active.is_(True)))
    ).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    mastery_avg = await db.scalar(
        select(func.avg(UserSkillState.p_known)).where(UserSkillState.user_id == user.id)
    )
    skills_mastered = await db.scalar(
        select(func.count(UserSkillState.id)).where(
            UserSkillState.user_id == user.id,
            mastered_clause(UserSkillState),
        )
    )

    cert_rows = await db.execute(
        select(Certificate, Track)
        .join(Track, Track.id == Certificate.track_id)
        .where(Certificate.user_id == user.id, Certificate.revoked.is_(False))
        .order_by(Certificate.issued_at.desc())
    )
    certificates = [
        PublicCertificateRead(
            code=cert.code,
            track_name_es=track.name_es,
            track_name_en=track.name_en,
            issued_at=cert.issued_at,
        )
        for cert, track in cert_rows.all()
    ]

    project_rows = await db.execute(
        select(ProjectSubmission, Project)
        .join(Project, Project.id == ProjectSubmission.project_id)
        .where(
            ProjectSubmission.user_id == user.id,
            ProjectSubmission.completed.is_(True),
            # 43.6: solo lo validado en el servidor es evidencia pública.
            ProjectSubmission.verified.is_(True),
        )
        .order_by(ProjectSubmission.completed_at.desc())
    )
    projects_completed = [
        PublicProjectRead(
            slug=project.slug,
            name_es=project.name_es,
            name_en=project.name_en,
            completed_at=submission.completed_at,  # type: ignore[arg-type]
        )
        for submission, project in project_rows.all()
    ]

    response.headers["Cache-Control"] = "public, max-age=300"
    return PublicProfileRead(
        username=user.username,
        display_name=user.display_name,
        avatar_emoji=user.avatar_emoji,
        joined_at=user.created_at,
        current_streak=user.current_streak,
        mastery_avg=round((mastery_avg or 0.0) * 100, 1),
        skills_mastered=skills_mastered or 0,
        certificates=certificates,
        projects_completed=projects_completed,
    )
