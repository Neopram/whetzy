"""Progress, mastery breakdown, and completion-time prediction endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.progress import (
    CurriculumResponse,
    DashboardResponse,
    DecayingSkill,
    DomainThresholds,
    PredictionResponse,
    SkillMasteryDetail,
)
from app.services import progress as progress_service
from app.services.churn import ChurnRiskResult, compute_risk
from app.services.engine.domain_thresholds import (
    DEFAULT_MODULE_UNLOCK_MASTERY,
    MASTERY_THRESHOLD,
)

router = APIRouter()


@router.get("/thresholds", response_model=DomainThresholds)
async def domain_thresholds(
    _: User = Depends(get_current_user),
) -> DomainThresholds:
    """The motor's canonical domain thresholds (C.1) — no DB lookup, these
    are fixed per deployment, not per user."""
    return DomainThresholds(
        mastery_threshold=MASTERY_THRESHOLD,
        default_module_unlock_mastery=DEFAULT_MODULE_UNLOCK_MASTERY,
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    return await progress_service.get_dashboard(db, current_user)


@router.get("/skills", response_model=list[SkillMasteryDetail])
async def skills_breakdown(
    track_id: str | None = Query(default=None),
    module_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SkillMasteryDetail]:
    return await progress_service.get_skill_breakdown(db, current_user, track_id, module_id)


@router.get("/decaying", response_model=list[DecayingSkill])
async def decaying_skills(
    within_days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=5, ge=1, le=20),
    track_id: str | None = Query(default=None, max_length=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DecayingSkill]:
    """Skills about to decay, soonest first — FSRS made visible. Con
    `track_id`, solo las de esa ruta (43.4: Hoy enseña la ruta activa)."""
    return await progress_service.get_decaying_skills(
        db, current_user, within_days=within_days, limit=limit, track_id=track_id
    )


@router.get("/curriculum", response_model=CurriculumResponse)
async def curriculum(
    track_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CurriculumResponse:
    return await progress_service.get_curriculum(db, current_user, track_id)


@router.get("/predictions", response_model=PredictionResponse)
async def predictions(
    track_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    return await progress_service.get_predictions(db, current_user, track_id)


@router.get("/risk", response_model=ChurnRiskResult)
async def churn_risk(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChurnRiskResult:
    """Return churn-risk score (0–1) and contributing factors for the current user."""
    return await compute_risk(db, current_user)
