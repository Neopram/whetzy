"""Paddle Billing, pago web (H.29).

Firma y forma de los eventos según developer.paddle.com (leído el 2026-10-01):
`Paddle-Signature: ts=..;h1=..`, HMAC-SHA256 de `"ts:cuerpo"` con la clave del
destino de notificaciones, 5 s de tolerancia.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.core.config import Settings, settings
from app.core.entitlements import user_meets_tier
from app.models.analytics import AnalyticsEvent
from app.models.content import Track
from app.models.exam import CertificationPurchase
from app.services import account_deletion, paddle_billing

SECRET = "pdl_ntfset_test_secret"
PLUS, PRO, CERT = "pri_plus_test", "pri_pro_test", "pri_cert_test"
WEBHOOK = "/api/v1/webhooks/paddle"


@pytest.fixture(autouse=True)
def paddle_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "PADDLE_WEBHOOK_SECRET", SECRET)
    monkeypatch.setattr(settings, "PADDLE_PRICE_PLUS", PLUS)
    monkeypatch.setattr(settings, "PADDLE_PRICE_PRO", PRO)
    monkeypatch.setattr(settings, "PADDLE_PRICE_CERTIFICATION", CERT)
    monkeypatch.setattr(settings, "PADDLE_WEBHOOK_TOLERANCE_SECONDS", 5)


def _sign(body: bytes, ts: int | None = None, secret: str = SECRET) -> str:
    ts = int(time.time()) if ts is None else ts
    h1 = hmac.new(secret.encode(), f"{ts}:".encode() + body, hashlib.sha256).hexdigest()
    return f"ts={ts};h1={h1}"


def _sub(user_id, *, price=PLUS, status="active", sub_id="sub_01test", **extra) -> dict:
    ends = (datetime.now(UTC) + timedelta(days=30)).isoformat()
    data = {
        "id": sub_id,
        "status": status,
        "items": [{"price": {"id": price}}],
        "current_billing_period": {"starts_at": datetime.now(UTC).isoformat(), "ends_at": ends},
        "scheduled_change": None,
        "custom_data": {"user_id": str(user_id)},
        "canceled_at": None,
    }
    data.update(extra)
    return data


def _event(event_type: str, data: dict) -> bytes:
    return json.dumps({
        "event_id": "evt_01test", "event_type": event_type,
        "occurred_at": datetime.now(UTC).isoformat(), "notification_id": "ntf_01test",
        "data": data,
    }).encode()


# ── Firma ─────────────────────────────────────────────────────────────────────


def test_a_valid_signature_is_accepted() -> None:
    body = _event("subscription.created", {"id": "sub_1"})
    assert paddle_billing.verify_webhook(body, _sign(body))["event_type"] == "subscription.created"


@pytest.mark.parametrize("case", ["wrong_secret", "tampered", "too_old", "missing", "malformed"])
def test_bad_signatures_are_rejected(case: str) -> None:
    body = _event("subscription.created", {"id": "sub_1"})
    header = {
        "wrong_secret": _sign(body, secret="otra"),
        "tampered": _sign(body),
        "too_old": _sign(body, ts=int(time.time()) - 60),
        "missing": None,
        "malformed": "h1=abc",
    }[case]
    payload = body.replace(b"sub_1", b"sub_2") if case == "tampered" else body
    with pytest.raises(ValueError):
        paddle_billing.verify_webhook(payload, header)


def test_signature_is_over_timestamp_and_body_not_body_alone() -> None:
    """El formato viejo del código (HMAC solo del cuerpo) ya no vale."""
    body = _event("subscription.created", {"id": "sub_1"})
    ts = int(time.time())
    body_only = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    with pytest.raises(ValueError):
        paddle_billing.verify_webhook(body, f"ts={ts};h1={body_only}")


def test_one_matching_h1_during_key_rotation_is_enough() -> None:
    body = _event("subscription.created", {"id": "sub_1"})
    good = _sign(body)
    ts, h1 = good.split(";")
    assert paddle_billing.verify_webhook(body, f"{ts};h1=deadbeef;{h1}")


def test_whitespace_pasted_around_paddle_values_is_ignored() -> None:
    """Un espacio o salto de línea pegado en Railway no rompe la firma."""
    padded = Settings(
        PADDLE_WEBHOOK_SECRET=f"  {SECRET}\n",
        PADDLE_API_KEY=" pdl_live_apikey_x\n",
        PADDLE_PRICE_PLUS=f"{PLUS} ",
        PADDLE_ENVIRONMENT="production\n",
    )
    assert padded.PADDLE_WEBHOOK_SECRET == SECRET
    assert padded.PADDLE_API_KEY == "pdl_live_apikey_x"
    assert padded.PADDLE_PRICE_PLUS == PLUS
    assert padded.PADDLE_ENVIRONMENT == "production"


def test_unconfigured_rail_raises_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "PADDLE_WEBHOOK_SECRET", "")
    body = _event("subscription.created", {"id": "sub_1"})
    with pytest.raises(RuntimeError):
        paddle_billing.verify_webhook(body, _sign(body))


# ── Suscripción → plan ────────────────────────────────────────────────────────


def test_active_subscription_grants_the_mapped_tier(user) -> None:
    assert paddle_billing.apply_subscription_event(user, "subscription.created", _sub(user.id))
    assert (user.subscription_tier, user.subscription_status, user.subscription_provider) == ("plus", "active", "paddle")
    assert user.is_premium is True
    assert user.paddle_subscription_id == "sub_01test"
    assert user.subscription_expires_at > datetime.now(UTC) + timedelta(days=29)
    assert user_meets_tier(user, "plus") and not user_meets_tier(user, "pro")


def test_the_pro_max_price_maps_to_pro(user) -> None:
    paddle_billing.apply_subscription_event(user, "subscription.created", _sub(user.id, price=PRO))
    assert user.subscription_tier == "pro" and user_meets_tier(user, "pro")


def test_scheduled_cancel_keeps_access_until_period_end(user) -> None:
    data = _sub(user.id, scheduled_change={"action": "cancel", "effective_at": "x"})
    paddle_billing.apply_subscription_event(user, "subscription.updated", data)
    assert user.subscription_status == "canceled"
    assert user.is_premium is True and user_meets_tier(user, "plus")


def test_canceled_subscription_removes_access(user) -> None:
    paddle_billing.apply_subscription_event(user, "subscription.created", _sub(user.id))
    data = _sub(user.id, status="canceled", canceled_at=datetime.now(UTC).isoformat())
    paddle_billing.apply_subscription_event(user, "subscription.canceled", data)
    assert user.is_premium is False
    assert not user_meets_tier(user, "plus")


def test_past_due_keeps_access_while_paddle_retries(user) -> None:
    paddle_billing.apply_subscription_event(user, "subscription.updated", _sub(user.id, status="past_due"))
    assert user.subscription_status == "past_due" and user_meets_tier(user, "plus")


def test_paused_subscription_removes_access(user) -> None:
    paddle_billing.apply_subscription_event(user, "subscription.created", _sub(user.id))
    paddle_billing.apply_subscription_event(user, "subscription.paused", _sub(user.id, status="paused"))
    assert not user_meets_tier(user, "plus")


def test_an_unknown_price_leaves_the_user_alone(user) -> None:
    assert paddle_billing.apply_subscription_event(user, "subscription.created", _sub(user.id, price="pri_otro")) is False
    assert user.subscription_tier is None and user.is_premium is False


# ── Endpoint ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_webhook_grants_the_plan_and_counts_one_conversion(client, db_session, user) -> None:
    body = _event("subscription.created", _sub(user.id))
    r = await client.post(WEBHOOK, content=body, headers={"Paddle-Signature": _sign(body)})
    assert r.status_code == 200, r.text
    renewal = _event("subscription.updated", _sub(user.id))
    r = await client.post(WEBHOOK, content=renewal, headers={"Paddle-Signature": _sign(renewal)})
    assert r.status_code == 200

    await db_session.refresh(user)
    assert user.subscription_tier == "plus" and user.is_premium is True
    started = await db_session.execute(
        select(func.count()).select_from(AnalyticsEvent).where(
            AnalyticsEvent.user_id == user.id, AnalyticsEvent.event_type == "subscription_started"
        )
    )
    assert started.scalar_one() == 1


@pytest.mark.asyncio
async def test_webhook_rejects_a_bad_signature(client, user) -> None:
    body = _event("subscription.created", _sub(user.id))
    r = await client.post(WEBHOOK, content=body, headers={"Paddle-Signature": _sign(body, secret="x")})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_webhook_without_secret_configured_is_503(client, user, monkeypatch) -> None:
    monkeypatch.setattr(settings, "PADDLE_WEBHOOK_SECRET", "")
    body = _event("subscription.created", _sub(user.id))
    r = await client.post(WEBHOOK, content=body, headers={"Paddle-Signature": "ts=1;h1=a"})
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_certification_transaction_records_the_purchase_once(client, db_session, user) -> None:
    db_session.add(Track(id="trkCERT", name_es="C", name_en="C", order=90, is_certification=True))
    await db_session.commit()
    data = {
        "id": "txn_01cert", "status": "completed", "subscription_id": None,
        "items": [{"price": {"id": CERT}}],
        "custom_data": {"user_id": str(user.id), "track_id": "trkCERT"},
    }
    for _ in range(2):  # Paddle reintenta: no debe duplicar
        body = _event("transaction.completed", data)
        r = await client.post(WEBHOOK, content=body, headers={"Paddle-Signature": _sign(body)})
        assert r.status_code == 200, r.text
    rows = (await db_session.execute(
        select(CertificationPurchase).where(CertificationPurchase.user_id == user.id)
    )).scalars().all()
    assert [(p.track_id, p.source, p.external_ref) for p in rows] == [("trkCERT", "paddle", "txn_01cert")]


@pytest.mark.asyncio
async def test_a_subscription_without_user_is_acknowledged_and_ignored(client, user) -> None:
    data = _sub(user.id)
    data["custom_data"] = {}
    body = _event("subscription.created", data)
    r = await client.post(WEBHOOK, content=body, headers={"Paddle-Signature": _sign(body)})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_public_config_is_disabled_until_configured(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "PADDLE_CLIENT_TOKEN", "")
    r = await client.get("/api/v1/billing/paddle/config")
    assert r.status_code == 200 and r.json()["enabled"] is False
    monkeypatch.setattr(settings, "PADDLE_CLIENT_TOKEN", "live_abc")
    monkeypatch.setattr(settings, "PADDLE_ENVIRONMENT", "production")
    cfg = (await client.get("/api/v1/billing/paddle/config")).json()
    assert cfg["enabled"] is True and cfg["environment"] == "production"
    assert cfg["prices"] == {"plus": PLUS, "pro": PRO, "certification": CERT}


# ── Borrar la cuenta cancela la suscripción ───────────────────────────────────


@pytest.mark.asyncio
async def test_deleting_the_account_cancels_the_paddle_subscription(db_session, user, monkeypatch) -> None:
    calls: list[str] = []

    async def fake_cancel(sub_id: str, *, immediately: bool = False) -> bool:
        calls.append(sub_id)
        return True

    monkeypatch.setattr(paddle_billing, "cancel_subscription", fake_cancel)
    paddle_billing.apply_subscription_event(user, "subscription.created", _sub(user.id))
    await db_session.commit()

    await account_deletion.request_deletion(db_session, user)
    assert calls == ["sub_01test"]


@pytest.mark.asyncio
async def test_deleting_an_account_without_paddle_calls_nothing(db_session, user, monkeypatch) -> None:
    async def boom(*a, **k):
        raise AssertionError("no debía llamar a Paddle")

    monkeypatch.setattr(paddle_billing, "cancel_subscription", boom)
    await account_deletion.request_deletion(db_session, user)


@pytest.mark.asyncio
async def test_cancel_without_api_key_does_not_call_paddle(monkeypatch) -> None:
    monkeypatch.setattr(settings, "PADDLE_API_KEY", "")
    assert await paddle_billing.cancel_subscription("sub_x") is False


@pytest.mark.asyncio
async def test_cancel_posts_to_the_documented_endpoint(monkeypatch) -> None:
    seen: dict = {}

    class FakeResp:
        status_code = 200
        text = "{}"

    class FakeClient:
        def __init__(self, *a, **k): ...
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def post(self, url, headers=None, json=None):
            seen.update(url=url, auth=headers["Authorization"], body=json)
            return FakeResp()

    monkeypatch.setattr(settings, "PADDLE_API_KEY", "pdl_live_apikey_x")
    monkeypatch.setattr(settings, "PADDLE_ENVIRONMENT", "production")
    monkeypatch.setattr(paddle_billing.httpx, "AsyncClient", FakeClient)
    assert await paddle_billing.cancel_subscription("sub_9") is True
    assert seen == {
        "url": "https://api.paddle.com/subscriptions/sub_9/cancel",
        "auth": "Bearer pdl_live_apikey_x",
        "body": {"effective_from": "next_billing_period"},
    }


@pytest.mark.asyncio
async def test_a_subscription_payment_is_not_a_certification_purchase(client, db_session, user) -> None:
    db_session.add(Track(id="trkCERT2", name_es="C", name_en="C", order=91, is_certification=True))
    await db_session.commit()
    data = {
        "id": "txn_01sub", "status": "completed", "subscription_id": "sub_01test",
        "items": [{"price": {"id": PLUS}}],
        "custom_data": {"user_id": str(user.id), "track_id": "trkCERT2"},
    }
    body = _event("transaction.completed", data)
    r = await client.post(WEBHOOK, content=body, headers={"Paddle-Signature": _sign(body)})
    assert r.status_code == 200
    count = await db_session.execute(select(func.count()).select_from(CertificationPurchase))
    assert count.scalar_one() == 0
