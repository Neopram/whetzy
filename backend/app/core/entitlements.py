"""Server-side feature entitlements / tier gating (7.3).

Tier hierarchy: free < plus < pro < creator

Nombres de cara al usuario (ADR-41, dueño 2026-09-24): ``plus`` = **Pro**
($14.99/mes), ``pro`` = **Pro Max** ($19.99/mes), ``creator`` = **Creador**
($99.99/mes: todo lo de Pro Max + publicar bootcamps en el marketplace, con
80/20 de cada venta). Los ids internos no cambian: están en la base de datos
y en Stripe.

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

from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User

_TIER_RANK: dict[str | None, int] = {
    None: 0,
    "free": 0,
    "plus": 1,
    "pro": 2,
    "creator": 3,
}

# Tiers that count as "premium" even when subscription_tier is NULL
# (e.g. grandfathered is_premium accounts)
_PREMIUM_BYPASS_TIERS = {"plus", "pro", "creator"}


def user_meets_tier(user: User, minimum: str) -> bool:
    """Return True if *user* has at least the *minimum* tier.

    Users with ``is_premium=True`` but no explicit ``subscription_tier``
    are treated as "plus" for backwards compatibility.
    """
    effective_tier = user.subscription_tier
    if effective_tier is None and user.is_premium:
        effective_tier = "plus"
    return _TIER_RANK.get(effective_tier, 0) >= _TIER_RANK.get(minimum, 0)


def require_tier(minimum: str) -> Callable[[User], Awaitable[None]]:
    """FastAPI dependency factory — raises 403 if the user is below *minimum*."""

    async def _check(user: User = Depends(get_current_user)) -> None:
        if not user_meets_tier(user, minimum):
            tier_display = minimum.capitalize()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires a {tier_display} subscription.",
            )

    return _check
