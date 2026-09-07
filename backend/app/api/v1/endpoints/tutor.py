"""AI tutor endpoint: personalized, content-grounded explanations."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.ai import tutor as tutor_service

router = APIRouter()


class ExplainRequest(BaseModel):
    question_id: str
    # Short-term memory: prior turns from the current tutoring session.
    # Each entry must have "role" ("user"|"assistant") and "content".
    conversation_history: list[dict] | None = None


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
) -> ExplainResponse:
    result = await tutor_service.explain_question(
        db,
        current_user,
        payload.question_id,
        conversation_history=payload.conversation_history,
    )
    return ExplainResponse(**result)
