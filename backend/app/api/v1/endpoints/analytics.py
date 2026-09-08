"""Analytics funnel endpoint (5.4)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.content import _require_admin_key
from app.core.db import get_db
from app.services.analytics import funnel

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
