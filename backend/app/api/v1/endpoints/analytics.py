"""Analytics endpoints (5.4 / 5.5)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.content import _require_admin_key
from app.core.db import get_db
from app.services.analytics import engagement, funnel, skill_mastery_stats

router = APIRouter()


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
    """Full analytics dashboard: funnel + engagement + skill mastery.

    Combines all four sections required for a product dashboard:
    - funnel     — registration → quiz → D1 → D7 retention
    - retention  — D1/D7 rates (extracted from funnel)
    - engagement — DAU trend, sessions/user, avg session duration
    - skill_mastery — top/bottom 5 skills by average p_known

    Requires X-Admin-Key header matching CONTENT_ADMIN_KEY env var.
    """
    funnel_data = await funnel(db, period_days=period_days)
    engagement_data = await engagement(db, period_days=engagement_days)
    mastery_data = await skill_mastery_stats(db)

    return {
        "funnel": funnel_data,
        "retention": {
            "d1_rate": funnel_data["d1_rate"],
            "d7_rate": funnel_data["d7_rate"],
            "d1_count": funnel_data["d1_return"],
            "d7_count": funnel_data["d7_return"],
        },
        "engagement": engagement_data,
        "skill_mastery": mastery_data,
    }
