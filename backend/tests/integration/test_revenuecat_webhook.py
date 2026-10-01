"""Integration tests for RevenueCat webhook (17.14 — mobile IAP, sandbox).

Event shapes and the Authorization-header auth mechanism match RevenueCat's
public docs (verified live 2026-09-27, see revenuecat_service.py's module
docstring) — no real RevenueCat credentials needed, these are recorded/
constructed sample events, not live calls.

Covers:
- POST /billing/revenuecat/webhook when not configured → 503
- POST /billing/revenuecat/webhook wrong/missing Authorization → 400
- INITIAL_PURCHASE → activates subscription, tier from entitlement_ids
- RENEWAL → refreshes expiry
- CANCELLATION → status=canceled, access NOT revoked immediately (39.31 handles the cutoff)
- EXPIRATION → is_premium False, status=expired
- unknown entitlement_id → no-op (200, user untouched)
- unknown app_user_id → no-op 200
- GET /billing/subscription reports subscription_provider
"""

from __future__ import annotations

import itertools
import json
import time
import uuid

from sqlalchemy import select

from app.core.security import create_access_token
from app.models.analytics import AnalyticsEvent
from app.models.user import User

BILLING = "/api/v1/billing"
_ip_counter = itertools.count(500)

FAKE_AUTH = "rc_whsec_test_fake"
ENTITLEMENT_PLUS = "plus_entitlement"
ENTITLEMENT_PRO = "pro_entitlement"


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


def _event(event_type: str, app_user_id: str, **extra) -> bytes:
    body = {
        "event": {
            "type": event_type,
            "id": str(uuid.uuid4()),
            "app_user_id": app_user_id,
            "environment": "SANDBOX",
            "event_timestamp_ms": int(time.time() * 1000),
            "store": "PLAY_STORE",
            **extra,
        },
        "api_version": "1.0",
    }
    return json.dumps(body).encode()


def _rc_headers(configured: bool = True) -> dict:
    return {**_h(), "Authorization": FAKE_AUTH if configured else "wrong-secret", "Content-Type": "application/json"}


async def test_webhook_returns_503_when_not_configured(client):
    payload = _event("INITIAL_PURCHASE", str(uuid.uuid4()))
    r = await client.post(
        f"{BILLING}/revenuecat/webhook",
        content=payload,
        headers={**_h(), "Content-Type": "application/json"},
    )
    assert r.status_code == 503


async def test_webhook_wrong_authorization_returns_400(client, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.REVENUECAT_WEBHOOK_AUTHORIZATION", FAKE_AUTH)
    payload = _event("INITIAL_PURCHASE", str(uuid.uuid4()))
    r = await client.post(
        f"{BILLING}/revenuecat/webhook",
        content=payload,
        headers=_rc_headers(configured=False),
    )
    assert r.status_code == 400


async def test_webhook_missing_authorization_returns_400(client, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.REVENUECAT_WEBHOOK_AUTHORIZATION", FAKE_AUTH)
    payload = _event("INITIAL_PURCHASE", str(uuid.uuid4()))
    r = await client.post(
        f"{BILLING}/revenuecat/webhook",
        content=payload,
        headers={**_h(), "Content-Type": "application/json"},
    )
    assert r.status_code == 400


async def test_initial_purchase_activates_subscription(client, user, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.REVENUECAT_WEBHOOK_AUTHORIZATION", FAKE_AUTH)
    monkeypatch.setattr("app.core.config.settings.REVENUECAT_ENTITLEMENT_PLUS", ENTITLEMENT_PLUS)

    expires_ms = int(time.time() * 1000) + 30 * 86400 * 1000
    payload = _event(
        "INITIAL_PURCHASE",
        str(user.id),
        entitlement_ids=[ENTITLEMENT_PLUS],
        expiration_at_ms=expires_ms,
    )

    r = await client.post(f"{BILLING}/revenuecat/webhook", content=payload, headers=_rc_headers())
    assert r.status_code == 200, r.text
    assert r.json()["received"] is True

    await db_session.refresh(user)
    assert user.is_premium is True
    assert user.subscription_tier == "plus"
    assert user.subscription_status == "active"
    assert user.subscription_provider == "revenuecat"
    assert user.subscription_expires_at is not None

    # 37.20: the false->true transition fires subscription_started exactly once.
    events = (
        await db_session.execute(
            select(AnalyticsEvent).where(
                AnalyticsEvent.user_id == user.id,
                AnalyticsEvent.event_type == "subscription_started",
            )
        )
    ).scalars().all()
    assert len(events) == 1


async def test_renewal_refreshes_expiry(client, user, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.REVENUECAT_WEBHOOK_AUTHORIZATION", FAKE_AUTH)
    monkeypatch.setattr("app.core.config.settings.REVENUECAT_ENTITLEMENT_PRO", ENTITLEMENT_PRO)

    user.is_premium = True
    user.subscription_tier = "pro"
    user.subscription_status = "active"
    user.subscription_provider = "revenuecat"
    await db_session.commit()

    new_expiry_ms = int(time.time() * 1000) + 60 * 86400 * 1000
    payload = _event(
        "RENEWAL",
        str(user.id),
        entitlement_ids=[ENTITLEMENT_PRO],
        expiration_at_ms=new_expiry_ms,
    )
    r = await client.post(f"{BILLING}/revenuecat/webhook", content=payload, headers=_rc_headers())
    assert r.status_code == 200

    await db_session.refresh(user)
    assert user.subscription_tier == "pro"
    assert user.is_premium is True

    # Already premium before the webhook fired — a renewal must not refire.
    events = (
        await db_session.execute(
            select(AnalyticsEvent).where(
                AnalyticsEvent.user_id == user.id,
                AnalyticsEvent.event_type == "subscription_started",
            )
        )
    ).scalars().all()
    assert len(events) == 0


async def test_cancellation_does_not_revoke_access_immediately(client, user, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.REVENUECAT_WEBHOOK_AUTHORIZATION", FAKE_AUTH)

    user.is_premium = True
    user.subscription_tier = "plus"
    user.subscription_status = "active"
    user.subscription_provider = "revenuecat"
    await db_session.commit()

    payload = _event("CANCELLATION", str(user.id))
    r = await client.post(f"{BILLING}/revenuecat/webhook", content=payload, headers=_rc_headers())
    assert r.status_code == 200

    await db_session.refresh(user)
    assert user.subscription_status == "canceled"
    # Still premium — access continues until subscription_expires_at (39.31).
    assert user.is_premium is True
    assert user.subscription_tier == "plus"


async def test_expiration_revokes_access(client, user, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.REVENUECAT_WEBHOOK_AUTHORIZATION", FAKE_AUTH)

    user.is_premium = True
    user.subscription_tier = "plus"
    user.subscription_status = "canceled"
    user.subscription_provider = "revenuecat"
    await db_session.commit()

    payload = _event("EXPIRATION", str(user.id))
    r = await client.post(f"{BILLING}/revenuecat/webhook", content=payload, headers=_rc_headers())
    assert r.status_code == 200

    await db_session.refresh(user)
    assert user.subscription_status == "expired"
    assert user.is_premium is False


async def test_unrecognized_entitlement_is_a_noop(client, user, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.REVENUECAT_WEBHOOK_AUTHORIZATION", FAKE_AUTH)
    monkeypatch.setattr("app.core.config.settings.REVENUECAT_ENTITLEMENT_PLUS", ENTITLEMENT_PLUS)

    payload = _event(
        "INITIAL_PURCHASE",
        str(user.id),
        entitlement_ids=["some_other_product_not_sold_here"],
        expiration_at_ms=int(time.time() * 1000) + 86400_000,
    )
    r = await client.post(f"{BILLING}/revenuecat/webhook", content=payload, headers=_rc_headers())
    assert r.status_code == 200

    await db_session.refresh(user)
    assert user.is_premium is False
    assert user.subscription_tier is None


async def test_unknown_app_user_id_returns_200(client, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.REVENUECAT_WEBHOOK_AUTHORIZATION", FAKE_AUTH)
    monkeypatch.setattr("app.core.config.settings.REVENUECAT_ENTITLEMENT_PLUS", ENTITLEMENT_PLUS)

    payload = _event(
        "INITIAL_PURCHASE",
        str(uuid.uuid4()),  # no such user
        entitlement_ids=[ENTITLEMENT_PLUS],
        expiration_at_ms=int(time.time() * 1000) + 86400_000,
    )
    r = await client.post(f"{BILLING}/revenuecat/webhook", content=payload, headers=_rc_headers())
    assert r.status_code == 200
    assert r.json()["received"] is True


async def test_malformed_app_user_id_is_a_noop(client, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.REVENUECAT_WEBHOOK_AUTHORIZATION", FAKE_AUTH)
    payload = _event("INITIAL_PURCHASE", "not-a-uuid")
    r = await client.post(f"{BILLING}/revenuecat/webhook", content=payload, headers=_rc_headers())
    assert r.status_code == 200


async def test_get_subscription_reports_revenuecat_provider(client, user, db_session):
    user.is_premium = True
    user.subscription_tier = "plus"
    user.subscription_status = "active"
    user.subscription_provider = "revenuecat"
    await db_session.commit()

    r = await client.get(f"{BILLING}/subscription", headers=_h(_auth(user)))
    assert r.status_code == 200, r.text
    assert r.json()["subscription_provider"] == "revenuecat"
