"""Integration tests for Stripe billing (7.2).

Tests use unittest.mock to patch stripe calls — no real Stripe credentials
needed. Covers:
- POST /billing/checkout → returns checkout_url; persists stripe_customer_id
- POST /billing/checkout when Stripe not configured → 503
- POST /billing/webhook checkout.session.completed → activates subscription
- POST /billing/webhook subscription.updated → updates status/tier
- POST /billing/webhook subscription.deleted → cancels subscription
- POST /billing/webhook missing signature → 400
- POST /billing/webhook unknown customer → no-op 200
- GET /billing/subscription → returns current state
"""

from __future__ import annotations

import hashlib
import hmac
import itertools
import json
import time
from unittest.mock import MagicMock

from app.core.security import create_access_token
from app.models.user import User

BILLING = "/api/v1/billing"
_ip_counter = itertools.count(400)

FAKE_CUSTOMER_ID = "cus_test_abc123"
FAKE_SUB_ID = "sub_test_xyz789"
FAKE_PRICE_PLUS = "price_plus_test"
FAKE_CHECKOUT_URL = "https://checkout.stripe.com/test/session"


def _ip() -> str:
    n = next(_ip_counter)
    return f"198.51.100.{n % 255 or 255}"


def _h(extra: dict | None = None) -> dict:
    headers = {"X-Forwarded-For": _ip()}
    if extra:
        headers.update(extra)
    return headers


def _auth(user: User) -> dict:
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


def _fake_sub(status: str = "active", price_id: str = FAKE_PRICE_PLUS) -> dict:
    return {
        "id": FAKE_SUB_ID,
        "status": status,
        "current_period_end": int(time.time()) + 30 * 86400,
        "items": {
            "data": [
                {
                    "price": {
                        "id": price_id,
                    }
                }
            ]
        },
    }


def _fake_stripe_event(event_type: str, data_object: dict) -> dict:
    return {
        "type": event_type,
        "data": {"object": data_object},
    }


def _stripe_sig(payload: bytes, secret: str = "whsec_test") -> str:
    ts = str(int(time.time()))
    signed = f"{ts}.{payload.decode()}"
    sig = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


# ── Checkout ──────────────────────────────────────────────────────────────────


async def test_checkout_creates_session(client, user, db_session, monkeypatch):
    monkeypatch.setattr("app.services.stripe_service.stripe", _make_stripe_mock())
    monkeypatch.setattr("app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setattr("app.core.config.settings.STRIPE_PRICE_PLUS", FAKE_PRICE_PLUS)

    r = await client.post(
        f"{BILLING}/checkout",
        json={"price_id": FAKE_PRICE_PLUS},
        headers=_h(_auth(user)),
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["checkout_url"] == FAKE_CHECKOUT_URL

    await db_session.refresh(user)
    assert user.stripe_customer_id == FAKE_CUSTOMER_ID


async def test_checkout_returns_503_when_not_configured(client, user):
    r = await client.post(
        f"{BILLING}/checkout",
        json={"price_id": FAKE_PRICE_PLUS},
        headers=_h(_auth(user)),
    )
    assert r.status_code == 503


async def test_checkout_requires_auth(client):
    r = await client.post(
        f"{BILLING}/checkout",
        json={"price_id": FAKE_PRICE_PLUS},
        headers=_h(),
    )
    assert r.status_code == 401


# ── Webhook ───────────────────────────────────────────────────────────────────


async def test_webhook_checkout_completed_activates_subscription(
    client, user, db_session, monkeypatch
):
    # Pre-set stripe_customer_id so webhook can find the user
    user.stripe_customer_id = FAKE_CUSTOMER_ID
    await db_session.commit()

    mock_stripe = _make_stripe_mock()
    monkeypatch.setattr("app.services.stripe_service.stripe", mock_stripe)
    monkeypatch.setattr("app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setattr("app.core.config.settings.STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr("app.core.config.settings.STRIPE_PRICE_PLUS", FAKE_PRICE_PLUS)

    event_obj = {
        "subscription": FAKE_SUB_ID,
        "customer": FAKE_CUSTOMER_ID,
    }
    event = _fake_stripe_event("checkout.session.completed", event_obj)
    payload = json.dumps(event).encode()
    sig = _stripe_sig(payload)

    # Override construct_event to return our fake event (bypass real HMAC)
    mock_stripe.Webhook.construct_event = MagicMock(return_value=event)

    r = await client.post(
        f"{BILLING}/webhook",
        content=payload,
        headers={**_h(), "stripe-signature": sig, "Content-Type": "application/json"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["received"] is True

    await db_session.refresh(user)
    assert user.is_premium is True
    assert user.stripe_subscription_id == FAKE_SUB_ID
    assert user.subscription_status == "active"
    assert user.subscription_tier == "plus"


async def test_webhook_subscription_deleted_cancels(client, user, db_session, monkeypatch):
    user.stripe_customer_id = FAKE_CUSTOMER_ID
    user.stripe_subscription_id = FAKE_SUB_ID
    user.is_premium = True
    user.subscription_status = "active"
    await db_session.commit()

    mock_stripe = _make_stripe_mock()
    monkeypatch.setattr("app.services.stripe_service.stripe", mock_stripe)
    monkeypatch.setattr("app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setattr("app.core.config.settings.STRIPE_WEBHOOK_SECRET", "whsec_test")

    event_obj = {"id": FAKE_SUB_ID, "customer": FAKE_CUSTOMER_ID, "status": "canceled"}
    event = _fake_stripe_event("customer.subscription.deleted", event_obj)
    payload = json.dumps(event).encode()
    mock_stripe.Webhook.construct_event = MagicMock(return_value=event)

    r = await client.post(
        f"{BILLING}/webhook",
        content=payload,
        headers={**_h(), "stripe-signature": "t=1,v1=fake", "Content-Type": "application/json"},
    )
    assert r.status_code == 200, r.text

    await db_session.refresh(user)
    assert user.is_premium is False
    assert user.subscription_status == "canceled"


async def test_webhook_missing_signature_returns_400(client):
    r = await client.post(
        f"{BILLING}/webhook",
        content=b"{}",
        headers=_h({"Content-Type": "application/json"}),
    )
    assert r.status_code == 400


async def test_webhook_unknown_customer_returns_200(client, monkeypatch):
    mock_stripe = _make_stripe_mock()
    monkeypatch.setattr("app.services.stripe_service.stripe", mock_stripe)
    monkeypatch.setattr("app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setattr("app.core.config.settings.STRIPE_WEBHOOK_SECRET", "whsec_test")

    event_obj = {"id": FAKE_SUB_ID, "customer": "cus_unknown_999", "status": "active"}
    event = _fake_stripe_event("customer.subscription.updated", event_obj)
    payload = json.dumps(event).encode()
    mock_stripe.Webhook.construct_event = MagicMock(return_value=event)

    r = await client.post(
        f"{BILLING}/webhook",
        content=payload,
        headers={**_h(), "stripe-signature": "t=1,v1=fake", "Content-Type": "application/json"},
    )
    assert r.status_code == 200
    assert r.json()["received"] is True


async def test_webhook_subscription_updated(client, user, db_session, monkeypatch):
    user.stripe_customer_id = FAKE_CUSTOMER_ID
    user.stripe_subscription_id = FAKE_SUB_ID
    user.is_premium = True
    user.subscription_status = "active"
    await db_session.commit()

    mock_stripe = _make_stripe_mock()
    monkeypatch.setattr("app.services.stripe_service.stripe", mock_stripe)
    monkeypatch.setattr("app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setattr("app.core.config.settings.STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr("app.core.config.settings.STRIPE_PRICE_PLUS", FAKE_PRICE_PLUS)

    sub = _fake_sub(status="past_due", price_id=FAKE_PRICE_PLUS)
    sub["customer"] = FAKE_CUSTOMER_ID
    event = _fake_stripe_event("customer.subscription.updated", sub)
    payload = json.dumps(event).encode()
    mock_stripe.Webhook.construct_event = MagicMock(return_value=event)

    r = await client.post(
        f"{BILLING}/webhook",
        content=payload,
        headers={**_h(), "stripe-signature": "t=1,v1=fake", "Content-Type": "application/json"},
    )
    assert r.status_code == 200

    await db_session.refresh(user)
    assert user.subscription_status == "past_due"
    assert user.is_premium is False  # past_due is not active/trialing


# ── Subscription state ────────────────────────────────────────────────────────


async def test_get_subscription_free_user(client, user):
    r = await client.get(f"{BILLING}/subscription", headers=_h(_auth(user)))
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["is_premium"] is False
    assert data["subscription_status"] is None
    assert data["subscription_tier"] is None


async def test_get_subscription_premium_user(client, user, db_session, monkeypatch):
    user.is_premium = True
    user.subscription_status = "active"
    user.subscription_tier = "plus"
    user.stripe_customer_id = FAKE_CUSTOMER_ID
    user.stripe_subscription_id = FAKE_SUB_ID
    await db_session.commit()

    r = await client.get(f"{BILLING}/subscription", headers=_h(_auth(user)))
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["is_premium"] is True
    assert data["subscription_status"] == "active"
    assert data["subscription_tier"] == "plus"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_stripe_mock() -> MagicMock:
    mock = MagicMock()

    # Customer.create
    mock.Customer.create.return_value = {"id": FAKE_CUSTOMER_ID}

    # checkout.Session.create
    mock.checkout = MagicMock()
    mock.checkout.Session.create.return_value = {"url": FAKE_CHECKOUT_URL}

    # Subscription.retrieve (used by checkout.session.completed)
    mock.Subscription.retrieve.return_value = _fake_sub()

    # Webhook.construct_event — default passthrough; tests override per-case
    mock.Webhook.construct_event = MagicMock(return_value={})

    return mock
