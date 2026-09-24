"""Leagues, badges, and daily missions endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.gamification import (
    LeagueHistoryEntry,
    LeagueStandingsResponse,
    UserBadgeWithDetail,
    UserMissionRead,
)
from app.services.gamification import service as gamification_service

router = APIRouter()


@router.get("/league/current", response_model=LeagueStandingsResponse)
async def current_league(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeagueStandingsResponse:
    standings = await gamification_service.get_current_standings(db, current_user)
    if standings is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "No leagues configured yet — seed at least one League"
        )
    return standings


class LeagueParticipationRequest(BaseModel):
    participate: bool


@router.put("/league/participation", response_model=LeagueStandingsResponse)
async def league_participation(
    body: LeagueParticipationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeagueStandingsResponse:
    """Entrar o salir de las ligas (35.4). Salir no toca XP, nivel ni racha."""
    standings = await gamification_service.set_league_participation(db, current_user, body.participate)
    if standings is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "No leagues configured yet — seed at least one League"
        )
    return standings


@router.get("/league/history", response_model=list[LeagueHistoryEntry])
async def league_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LeagueHistoryEntry]:
    return await gamification_service.get_league_history(db, current_user)


@router.get("/badges", response_model=list[UserBadgeWithDetail])
async def badges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserBadgeWithDetail]:
    return await gamification_service.get_user_badges(db, current_user)


@router.get("/missions", response_model=list[UserMissionRead])
async def missions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserMissionRead]:
    return await gamification_service.get_today_missions(db, current_user)
