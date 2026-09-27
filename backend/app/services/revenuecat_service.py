"""RevenueCat webhook processing — mobile in-app purchases (17.14).

Sandbox-only until the owner activates live App Store/Play Store keys
(H.2, H.3): REVENUECAT_WEBHOOK_AUTHORIZATION empty means this rail is off.

Design mirrors stripe_service.py's shape (verify_webhook + apply_subscription_
event) so both rails read as the same pattern, but they are not behind a
shared Python interface — the actual shared contract is the User columns
both write (subscription_tier/status/expires_at/is_premium/provider) and
core/entitlements.user_meets_tier, which neither rail bypasses. Wrapping that
in an ABC would duplicate the contract, not add one, and risks the live,
tested Stripe path for no behavioral gain (see the migration's docstring).

Field names and the Authorization-header auth mechanism verified live against
https://www.revenuecat.com/docs/integrations/webhooks and
https://www.revenuecat.com/docs/integrations/webhooks/event-types-and-fields
(2026-09-27) — RevenueCat also offers an *optional* HMAC-SHA256 signature
(X-RevenueCat-Webhook-Signature); this only implements the Authorization
header, the one always-available mechanism ("the only option for security
for the Webhooks tool" per RevenueCat's own docs at the time of writing).
"""

from __future__ import annotations

import hmac
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings
from app.models.user import User

# Lifecycle events that mean "the entitlement is active, (re)apply it".
_ACTIVATING_EVENTS = frozenset(
    {"INITIAL_PURCHASE", "RENEWAL", "PRODUCT_CHANGE", "UNCANCELLATION", "SUBSCRIPTION_EXTENDED"}
)
# CANCELLATION turns off auto-renew but access continues until expiration_at_ms
# — handled by the same lapsed-subscription check user_meets_tier already does
# (39.31), so it only needs the status label, not an immediate downgrade.
_CANCELLING_EVENTS = frozenset({"CANCELLATION"})
# The entitlement is actually gone.
_EXPIRING_EVENTS = frozenset({"EXPIRATION"})


def _configured() -> bool:
    return bool(settings.REVENUECAT_WEBHOOK_AUTHORIZATION)


def _entitlement_to_tier() -> dict[str, str]:
    m: dict[str, str] = {}
    if settings.REVENUECAT_ENTITLEMENT_PLUS:
        m[settings.REVENUECAT_ENTITLEMENT_PLUS] = "plus"
    if settings.REVENUECAT_ENTITLEMENT_PRO:
        m[settings.REVENUECAT_ENTITLEMENT_PRO] = "pro"
    return m


def verify_webhook(payload: bytes, authorization_header: str | None) -> dict[str, Any]:
    """Parse and authenticate a RevenueCat webhook request.

    Raises ``RuntimeError`` if the rail isn't configured (mirrors
    stripe_service.verify_webhook's own RuntimeError for the same case).
    Raises ``ValueError`` on a missing/wrong Authorization header or
    unparseable body — callers map both to 4xx, same as the Stripe endpoint.
    """
    if not _configured():
        raise RuntimeError("RevenueCat not configured: set REVENUECAT_WEBHOOK_AUTHORIZATION")
    if not authorization_header or not hmac.compare_digest(
        authorization_header, settings.REVENUECAT_WEBHOOK_AUTHORIZATION
    ):
        raise ValueError("Invalid Authorization header")
    try:
        body = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON body") from exc
    event = body.get("event")
    if not isinstance(event, dict):
        # ValueError, not TypeError: this is untrusted request data, not a
        # Python type bug — the caller catches ValueError alongside the
        # JSON-decode failure above and maps both to one 400 response.
        raise ValueError("Missing 'event' object")  # noqa: TRY004
    return event


def resolve_user_id(event: dict[str, Any]) -> uuid.UUID | None:
    """RevenueCat's app_user_id is the Whetzy user id (set at SDK init on the
    client, `Purchases.configure(apiKey, appUserID: user.id)`) — no separate
    id mapping to store or look up, unlike Stripe's own customer_id."""
    raw = event.get("app_user_id")
    if not raw:
        return None
    try:
        return uuid.UUID(str(raw))
    except ValueError:
        return None


def apply_subscription_event(user: User, event: dict[str, Any]) -> None:
    """Update *user* subscription state from a RevenueCat webhook event (in-place)."""
    event_type: str = event.get("type", "")

    if event_type in _ACTIVATING_EVENTS:
        entitlement_ids: list[str] = event.get("entitlement_ids") or []
        tier_map = _entitlement_to_tier()
        tier = next((tier_map[e] for e in entitlement_ids if e in tier_map), None)
        if tier is None:
            return  # entitlement we don't sell/recognize — leave the user alone
        user.subscription_tier = tier
        user.subscription_status = "active"
        user.subscription_provider = "revenuecat"
        user.is_premium = True
        expiration_ms = event.get("expiration_at_ms")
        if expiration_ms:
            user.subscription_expires_at = datetime.fromtimestamp(int(expiration_ms) / 1000, tz=UTC)

    elif event_type in _CANCELLING_EVENTS:
        user.subscription_status = "canceled"
        # Deliberately no is_premium/tier change: access continues until
        # subscription_expires_at, same grace period Stripe's cancel-at-
        # period-end flow gives (user_meets_tier already enforces the cutoff).

    elif event_type in _EXPIRING_EVENTS:
        user.subscription_status = "expired"
        user.is_premium = False
