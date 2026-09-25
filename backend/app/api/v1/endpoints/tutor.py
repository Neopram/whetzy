"""AI tutor endpoint: personalized, content-grounded explanations."""

from __future__ import annotations

from typing import Any

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
    result = await tutor_service.explain_question(
        db,
        current_user,
        payload.question_id,
        conversation_history=payload.conversation_history,
    )
    # Solo cuenta lo que se sirvió: un fallo del proveedor no gasta cupo.
    await tutor_quota.record(db, current_user.id, day)
    await db.commit()
    return ExplainResponse(**result)
