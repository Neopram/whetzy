"""Stripe checkout + webhook processing (7.2).

Thin wrapper around the stripe-python library so tests can patch it at
``app.services.stripe_service.stripe``.

Design decisions:
- We store stripe_customer_id on the User so we can re-use the customer
  across multiple checkout sessions rather than creating duplicates.
- Subscription tier is derived from the Stripe price ID at webhook time;
  mapping lives in PRICE_TO_TIER so it can be extended without code change.
- is_premium stays True for any active/trialing subscription; it is the
  field the rest of the app uses for feature gating (kept separate so 7.3
  can add finer-grained entitlements on top).
"""

from __future__ import annotations

from datetime import datetime, timezone

import stripe as _stripe

from app.core.config import settings
from app.models.user import User

stripe = _stripe  # aliased so tests can patch: patch("app.services.stripe_service.stripe")

PRICE_TO_TIER: dict[str, str] = {}  # populated at call time from settings


def _price_map() -> dict[str, str]:
    m: dict[str, str] = {}
    if settings.STRIPE_PRICE_PLUS:
        m[settings.STRIPE_PRICE_PLUS] = "plus"
    if settings.STRIPE_PRICE_PRO:
        m[settings.STRIPE_PRICE_PRO] = "pro"
    return m


def _configured() -> bool:
    return bool(settings.STRIPE_SECRET_KEY)


def create_checkout_session(user: User, price_id: str) -> str:
    """Return the Stripe-hosted checkout URL for *price_id*.

    Raises ``RuntimeError`` if Stripe is not configured (STRIPE_SECRET_KEY empty).
    """
    if not _configured():
        raise RuntimeError("Stripe not configured: set STRIPE_SECRET_KEY")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Re-use existing customer or create one
    if user.stripe_customer_id:
        customer_id = user.stripe_customer_id
    else:
        customer = stripe.Customer.create(email=user.email, metadata={"user_id": str(user.id)})
        customer_id = customer["id"]

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=settings.STRIPE_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=settings.STRIPE_CANCEL_URL,
        metadata={"user_id": str(user.id)},
    )
    # Persist customer_id even before checkout completes; idempotent on retry
    user.stripe_customer_id = customer_id
    return session["url"]


def verify_webhook(payload: bytes, sig_header: str) -> dict:
    """Parse and verify a Stripe webhook event.

    Raises ``stripe.error.SignatureVerificationError`` on bad signature.
    Raises ``RuntimeError`` if webhook secret is not configured.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise RuntimeError("Stripe webhook secret not configured: set STRIPE_WEBHOOK_SECRET")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    return dict(event)


def apply_subscription_event(user: User, event: dict) -> None:
    """Update *user* subscription state from a Stripe webhook event (in-place).

    Handles:
    - ``checkout.session.completed``   → activate subscription
    - ``customer.subscription.updated``→ update status/tier/expiry
    - ``customer.subscription.deleted``→ cancel subscription
    """
    event_type: str = event["type"]
    data_object: dict = event["data"]["object"]

    if event_type == "checkout.session.completed":
        sub_id: str = data_object.get("subscription", "")
        if not sub_id:
            return
        stripe.api_key = settings.STRIPE_SECRET_KEY
        sub = stripe.Subscription.retrieve(sub_id)
        _set_subscription(user, sub)

    elif event_type in ("customer.subscription.updated", "customer.subscription.created"):
        _set_subscription(user, data_object)

    elif event_type == "customer.subscription.deleted":
        user.subscription_status = "canceled"
        user.is_premium = False
        user.stripe_subscription_id = data_object.get("id") or user.stripe_subscription_id


def _set_subscription(user: User, sub: dict) -> None:
    tier_map = _price_map()
    user.stripe_subscription_id = sub["id"]
    user.subscription_status = sub["status"]
    user.is_premium = sub["status"] in ("active", "trialing")

    # Derive tier from first line item price
    items = sub.get("items", {}).get("data", [])
    price_id = items[0]["price"]["id"] if items else None
    user.subscription_tier = tier_map.get(price_id or "", None) if price_id else None

    # current_period_end is a Unix timestamp
    period_end = sub.get("current_period_end")
    if period_end:
        user.subscription_expires_at = datetime.fromtimestamp(int(period_end), tz=timezone.utc)
