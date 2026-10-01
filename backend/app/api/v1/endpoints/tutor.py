"""AI tutor endpoint: personalized, content-grounded explanations."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.entitlements import require_tier
from app.core.security import get_current_user
from app.models.user import User
from app.services import tutor_quota
from app.services.ai import tutor as tutor_service

router = APIRouter()
logger = logging.getLogger("whetzy.llm")

# 503 con este detalle cuando el proveedor rechaza la llamada y no hay respaldo
# que lo cubra (GuardedProvider deja pasar los 4xx a propósito, 39.11): el
# alumno ve «inténtalo de nuevo» y el log dice qué falla, en vez de un 500.
TUTOR_UNAVAILABLE = "tutor_unavailable"


class ExplainRequest(BaseModel):
    question_id: str
    # Short-term memory: prior turns from the current tutoring session.
    # Each entry must have "role" ("user"|"assistant") and "content".
    conversation_history: list[dict[str, Any]] | None = None


class ExplainResponse(BaseModel):
    explanation: str
    provider: str
    grounded: bool
    times_missed: int = 0


@router.post("/explain", response_model=ExplainResponse)
async def explain(
    payload: ExplainRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _tier: None = Depends(require_tier("plus")),
) -> ExplainResponse:
    # Pro tiene cupo diario; Pro Max, ilimitado (38.6, ADR-49).
    day = tutor_quota.today_utc()
    limit = tutor_quota.daily_limit(current_user)
    if (
        limit is not None
        and await tutor_quota.used_on(db, current_user.id, day) >= limit
    ):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail=tutor_quota.LIMIT_REACHED,
            headers={
                "X-Tutor-Daily-Limit": str(limit),
                "X-Tutor-Resets-At": tutor_quota.resets_at(day).isoformat(),
            },
        )
    try:
        result = await tutor_service.explain_question(
            db,
            current_user,
            payload.question_id,
            conversation_history=payload.conversation_history,
        )
    except httpx.HTTPStatusError as exc:
        logger.error(
            "llm_provider_rejected status=%s url=%s",
            exc.response.status_code,
            exc.request.url,
        )
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail=TUTOR_UNAVAILABLE
        ) from exc
    # Solo cuenta lo que se sirvió: un fallo del proveedor no gasta cupo.
    await tutor_quota.record(db, current_user.id, day)
    await db.commit()
    return ExplainResponse(**result)
