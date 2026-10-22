"""AI tutor endpoint: personalized, content-grounded explanations."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.entitlements import require_tier, user_meets_tier
from app.core.security import get_current_user
from app.models.content import Question
from app.models.exam import MockExamAttempt
from app.models.user import User
from app.services import tutor_quota
from app.services.ai import tutor as tutor_service
from app.services.ai.tutor import TutorMode

router = APIRouter()
logger = logging.getLogger("whetzy.llm")

# 503 con este detalle cuando el proveedor rechaza la llamada y no hay respaldo
# que lo cubra (GuardedProvider deja pasar los 4xx a propósito, 39.11): el
# alumno ve «inténtalo de nuevo» y el log dice qué falla, en vez de un 500.
TUTOR_UNAVAILABLE = "tutor_unavailable"

# 41.5: ninguno de los dos motivos daba 403 antes de esto — el tutor
# explicaba cualquier pregunta, incluida la del examen que el alumno tiene
# delante ahora mismo o cualquiera del banco reservado para simulacros.
QUESTION_RESERVED = "question_reserved"
EXAM_IN_PROGRESS = "exam_in_progress"


# Ola 2: «A fondo» es de Pro Max (decisión del dueño, 2026-10-21).
DEEP_REQUIRES_PRO_MAX = "deep_requires_pro_max"


class ExplainRequest(BaseModel):
    question_id: str
    mode: TutorMode = "why"
    # Short-term memory: prior turns from the current tutoring session.
    # Each entry must have "role" ("user"|"assistant") and "content".
    conversation_history: list[dict[str, Any]] | None = None


class ExplainResponse(BaseModel):
    explanation: str
    provider: str
    grounded: bool
    times_missed: int = 0
    mode: TutorMode = "why"


@router.post("/explain", response_model=ExplainResponse)
async def explain(
    payload: ExplainRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _tier: None = Depends(require_tier("plus")),
) -> ExplainResponse:
    # Antes de reservar cupo: pedir «A fondo» sin Pro Max no gasta nada.
    if payload.mode == "deep" and not user_meets_tier(current_user, "pro"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=DEEP_REQUIRES_PRO_MAX)

    # 41.5: ni la pregunta de un examen en curso ni ninguna del banco
    # reservado (pool == "simulacro") pasan por el tutor — explicarla
    # mientras cuenta para la nota, o explicar una que el alumno todavía no
    # ha visto en un simulacro, le daría la respuesta antes de que la
    # pregunta midiera nada.
    question = (
        await db.execute(select(Question).where(Question.id == payload.question_id))
    ).scalar_one_or_none()
    if question is not None:
        if question.pool == "simulacro":
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=QUESTION_RESERVED)
        active_attempts = (
            await db.execute(
                select(MockExamAttempt.question_ids).where(
                    MockExamAttempt.user_id == current_user.id,
                    MockExamAttempt.submitted_at.is_(None),
                    MockExamAttempt.expires_at > datetime.now(UTC),
                )
            )
        ).scalars().all()
        if any(payload.question_id in ids for ids in active_attempts):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=EXAM_IN_PROGRESS)

    # Pro tiene cupo diario de explicaciones; Pro Max, ilimitado (38.6,
    # ADR-49). El cupo por tokens (41.17) nunca bloquea a quien ADR-49 ya
    # declaró sin tope -- daily_token_limit devuelve None para esa misma
    # población.
    day = tutor_quota.today_utc()
    explanation_limit = tutor_quota.daily_limit(current_user)
    token_limit = tutor_quota.daily_token_limit(current_user)
    token_estimate = tutor_quota.TOKEN_RESERVE_ESTIMATE

    # 41.17: comprobar el cupo y reservarlo son el mismo UPDATE condicional
    # -- antes eran dos pasos separados por la latencia del LLM, y en esa
    # ventana dos peticiones a la vez podían ver las dos "cupo libre" (con
    # el límite en 20, Plus podía recibir 21). Si la reserva falla, ni
    # siquiera se llama al proveedor.
    reserved = await tutor_quota.reserve(
        db,
        current_user.id,
        day,
        explanation_limit=explanation_limit,
        token_limit=token_limit,
        token_estimate=token_estimate,
    )
    await db.commit()
    if not reserved:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail=tutor_quota.LIMIT_REACHED,
            headers={
                "X-Tutor-Daily-Limit": str(explanation_limit),
                "X-Tutor-Resets-At": tutor_quota.resets_at(day).isoformat(),
            },
        )

    try:
        result = await tutor_service.explain_question(
            db,
            current_user,
            payload.question_id,
            conversation_history=payload.conversation_history,
            mode=payload.mode,
        )
    except httpx.HTTPStatusError as exc:
        # Solo cuenta lo que de verdad se sirvió: un fallo del proveedor no
        # gasta cupo -- con la reserva atómica, eso ya significa devolverla.
        await tutor_quota.release(db, current_user.id, day, token_estimate=token_estimate)
        await db.commit()
        logger.error(
            "llm_provider_rejected status=%s url=%s",
            exc.response.status_code,
            exc.request.url,
        )
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail=TUTOR_UNAVAILABLE
        ) from exc
    # Solo cuenta lo que se sirvió: un fallo del proveedor no gasta cupo, y
    # tampoco lo hace el NullProvider al que cae un GuardedProvider
    # configurado cuando agota su cupo diario o falla la cadena entera
    # (41.5) — eso no es una explicación real, aunque responda 200.
    actual_tokens = result.pop("tokens_used", 0)
    if not result.pop("degraded_fallback", False):
        await tutor_quota.settle(
            db, current_user.id, day, token_estimate=token_estimate, actual_tokens=actual_tokens
        )
    else:
        await tutor_quota.release(db, current_user.id, day, token_estimate=token_estimate)
    await db.commit()
    return ExplainResponse(**result, mode=payload.mode)
