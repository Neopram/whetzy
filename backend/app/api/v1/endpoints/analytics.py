"""Analytics endpoints (5.4 / 5.5)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.content import _require_admin_key
from app.core.db import get_db
from app.core.rate_limiter import InMemoryRateLimiter
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.client_events import ClientEventBatch
from app.services.analytics import (
    PRODUCT_METRIC_TARGETS,
    conversion_d35,
    curr,
    engagement,
    funnel,
    fx_skip_rates,
    skill_mastery_stats,
    track,
    unseen_first_attempt_accuracy,
    weekly_30min_rate_among_payers,
)

router = APIRouter()

# 46.6a: un alumno real manda, como mucho, un lote cada 10 s y otro al cerrar.
_client_events_limiter = InMemoryRateLimiter()


@router.get("/funnel", dependencies=[Depends(_require_admin_key)])
async def get_funnel(
    period_days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Return registration → first-quiz → D1 → D7 funnel metrics.

    Requires X-Admin-Key header matching CONTENT_ADMIN_KEY env var.
    """
    return await funnel(db, period_days=period_days)


@router.get("/dashboard", dependencies=[Depends(_require_admin_key)])
async def get_dashboard(
    period_days: int = Query(default=30, ge=1, le=365),
    engagement_days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Full analytics dashboard: funnel + engagement + skill mastery + the
    37.20 (ADR-53 §8) product-metric floor — each number next to its target,
    never one without the other.

    Combines the sections required for a product dashboard:
    - funnel     — registration → quiz → D1/D7/D30 retention
    - retention  — D1/D7/D30 rates (extracted from funnel)
    - engagement — DAU trend, sessions/user, avg session duration
    - skill_mastery — top/bottom 5 skills by average p_known
    - curr — of the last 7 days' active users, % also active today
    - conversion_d35 — % converted to paid within 35 days of registering
      (only accurate for users who registered after `subscription_started`
      instrumentation shipped, 37.20; `sample_too_small` says so)
    - weekly_30min_among_payers — % of current payers with >=30 min this week
    - targets — the ADR-53 §8 floor for every metric above; two rows
      (track completion among payers, mock-exam-vs-real-exam calibration)
      have no live number yet — Whetzy has no track-completion signal and
      no way to learn a real exam's outcome — and are marked as such rather
      than approximated from a definition nobody signed off on.

    Requires X-Admin-Key header matching CONTENT_ADMIN_KEY env var.
    """
    funnel_data = await funnel(db, period_days=period_days)
    engagement_data = await engagement(db, period_days=engagement_days)
    mastery_data = await skill_mastery_stats(db)
    curr_data = await curr(db)
    conversion_data = await conversion_d35(db)
    weekly_30min_data = await weekly_30min_rate_among_payers(db)
    h4_data = await unseen_first_attempt_accuracy(db)

    return {
        "funnel": funnel_data,
        "retention": {
            "d1_rate": funnel_data["d1_rate"],
            "d7_rate": funnel_data["d7_rate"],
            "d30_rate": funnel_data["d30_rate"],
            "d1_count": funnel_data["d1_return"],
            "d7_count": funnel_data["d7_return"],
            "d30_count": funnel_data["d30_return"],
            # D-31: cada tasa con su cohorte, para leerla en personas («4 de 30»).
            "d1_cohort": funnel_data["d1_cohort"],
            "d7_cohort": funnel_data["d7_cohort"],
            "d30_cohort": funnel_data["d30_cohort"],
            "d1_rate_activated": funnel_data["d1_rate_activated"],
            "d7_rate_activated": funnel_data["d7_rate_activated"],
            "d30_rate_activated": funnel_data["d30_rate_activated"],
        },
        "engagement": engagement_data,
        "skill_mastery": mastery_data,
        "curr": curr_data,
        "conversion_d35": conversion_data,
        "weekly_30min_among_payers": weekly_30min_data,
        # H4: acierto al primer intento en preguntas no vistas, principio vs final.
        "learning_unseen_first_attempt": h4_data,
        "not_yet_measurable": {
            "completion_rate_among_payers": "sin señal de «track completado» en el modelo hoy",
            "mock_exam_calibration": "sin conexión con el resultado del examen real",
        },
        "targets": PRODUCT_METRIC_TARGETS,
    }


@router.post("/client-events", status_code=status.HTTP_202_ACCEPTED)
async def post_client_events(
    batch: ClientEventBatch,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    """46.6a (ADR-68): efectos del cliente, en lote.

    La sesión solo sirve para limitar el ritmo: las filas se guardan **sin
    `user_id`** ni IP (ADR-68 punto 3).
    """
    if not await _client_events_limiter.is_allowed(
        f"client-events:{current_user.id}", limit=30, window_seconds=60
    ):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate_limited")
    for e in batch.events:
        props = e.model_dump(exclude={"type"})
        await track(db, e.type, user_id=None, properties=props)
    await db.commit()
    return {"accepted": len(batch.events)}


@router.get("/fx", dependencies=[Depends(_require_admin_key)])
async def get_fx(
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """46.6a: tasa de salto por nivel y si toca rebajarlo (plan §6.0 punto 5)."""
    return await fx_skip_rates(db, days=days)
