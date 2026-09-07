"""Computer-adaptive placement test endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.placement import (
    PlacementAnswerRequest,
    PlacementAnswerResponse,
    PlacementResultResponse,
    PlacementStartRequest,
    PlacementStartResponse,
)
from app.services import placement as placement_service

router = APIRouter()


@router.post("/start", response_model=PlacementStartResponse)
async def start_placement(
    payload: PlacementStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlacementStartResponse:
    return await placement_service.start_placement(db, current_user, payload.track_id)


@router.post("/answer", response_model=PlacementAnswerResponse)
async def answer_placement(
    payload: PlacementAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlacementAnswerResponse:
    return await placement_service.answer_placement(
        db,
        current_user,
        session_id=payload.session_id,
        question_id=payload.question_id,
        selected_index=payload.selected_index,
        response_time_ms=payload.response_time_ms,
    )


@router.get("/result", response_model=PlacementResultResponse)
async def placement_result(
    session_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlacementResultResponse:
    return await placement_service.get_placement_result(db, current_user, session_id)
