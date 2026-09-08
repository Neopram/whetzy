"""Server-side feature entitlements / tier gating (7.3).

Tier hierarchy: free < plus < pro

Callers use ``require_tier`` as a FastAPI Depends factory:

    @router.get("/premium-feature")
    async def premium_feature(
        _: None = Depends(require_tier("plus")),
        user: User = Depends(get_current_user),
    ): ...

Or call ``user_meets_tier`` directly in endpoint bodies for conditional gating
(e.g. when a single endpoint accepts different modes with different tiers).
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User

_TIER_RANK: dict[str | None, int] = {
    None: 0,
    "free": 0,
    "plus": 1,
    "pro": 2,
}

# Tiers that count as "premium" even when subscription_tier is NULL
# (e.g. grandfathered is_premium accounts)
_PREMIUM_BYPASS_TIERS = {"plus", "pro"}


def user_meets_tier(user: User, minimum: str) -> bool:
    """Return True if *user* has at least the *minimum* tier.

    Users with ``is_premium=True`` but no explicit ``subscription_tier``
    are treated as "plus" for backwards compatibility.
    """
    effective_tier = user.subscription_tier
    if effective_tier is None and user.is_premium:
        effective_tier = "plus"
    return _TIER_RANK.get(effective_tier, 0) >= _TIER_RANK.get(minimum, 0)


def require_tier(minimum: str):
    """FastAPI dependency factory — raises 403 if the user is below *minimum*."""

    async def _check(user: User = Depends(get_current_user)) -> None:
        if not user_meets_tier(user, minimum):
            tier_display = minimum.capitalize()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires a {tier_display} subscription.",
            )

    return _check
