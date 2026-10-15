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
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.core.config import Settings, settings
from app.core.entitlements import user_meets_tier
from app.models.analytics import AnalyticsEvent
from app.models.content import Track
from app.models.exam import CertificationPurchase
from app.models.paddle_event import PaddleEvent
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


def _event(
    event_type: str, data: dict, *, event_id: str | None = None, occurred_at: datetime | None = None
) -> bytes:
    # Paddle da a cada evento un `event_id` único; desde D-10 el receptor
    # deduplica por él, así que reutilizar uno fijo haría pasar los eventos
    # siguientes por duplicados.
    return json.dumps({
        "event_id": event_id or f"evt_{uuid.uuid4().hex}", "event_type": event_type,
        "occurred_at": (occurred_at or datetime.now(UTC)).isoformat(),
        "notification_id": "ntf_01test",
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


def test_a_stale_cancel_for_an_old_subscription_does_not_touch_the_new_one(user) -> None:
    """Entrega de webhooks no garantiza orden: el `canceled` de la suscripción
    vieja puede llegar después de que el usuario ya pagó una nueva."""
    paddle_billing.apply_subscription_event(user, "subscription.created", _sub(user.id, sub_id="sub_old"))
    paddle_billing.apply_subscription_event(
        user, "subscription.created", _sub(user.id, price=PRO, sub_id="sub_new")
    )
    assert user.paddle_subscription_id == "sub_new" and user.is_premium is True

    stale = _sub(user.id, sub_id="sub_old", status="canceled", canceled_at=datetime.now(UTC).isoformat())
    applied = paddle_billing.apply_subscription_event(user, "subscription.canceled", stale)

    assert applied is False
    assert user.paddle_subscription_id == "sub_new"
    assert user.is_premium is True and user.subscription_tier == "pro"


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
async def test_webhook_records_the_eu_withdrawal_waiver_once(client, db_session, user) -> None:
    """La casilla del art. 16.m que exige /checkout queda guardada en el alumno."""
    data = _sub(user.id, custom_data={"user_id": str(user.id), "eu_withdrawal_waiver": "accepted"})
    body = _event("subscription.created", data)
    r = await client.post(WEBHOOK, content=body, headers={"Paddle-Signature": _sign(body)})
    assert r.status_code == 200, r.text
    await db_session.refresh(user)
    first = user.eu_withdrawal_waiver_at
    assert first is not None

    renewal = _event("subscription.updated", data)
    await client.post(WEBHOOK, content=renewal, headers={"Paddle-Signature": _sign(renewal)})
    await db_session.refresh(user)
    assert user.eu_withdrawal_waiver_at == first  # la primera aceptación, no la última


def test_no_waiver_in_custom_data_records_nothing(user) -> None:
    paddle_billing.record_withdrawal_waiver(user, _sub(user.id))
    assert user.eu_withdrawal_waiver_at is None


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
async def test_an_approved_refund_revokes_the_certification_purchase(client, db_session, user) -> None:
    """developer.paddle.com/webhooks/adjustments (verificado 2026-10-04):
    Paddle manda un reembolso como `adjustment.created`, no como un
    `transaction.refunded` — antes de esto nada lo escuchaba y el alumno
    reembolsado conservaba el examen certificador para siempre."""
    db_session.add(Track(id="trkCERT3", name_es="C", name_en="C", order=92, is_certification=True))
    await db_session.commit()
    purchase_data = {
        "id": "txn_01refund", "status": "completed", "subscription_id": None,
        "items": [{"price": {"id": CERT}}],
        "custom_data": {"user_id": str(user.id), "track_id": "trkCERT3"},
    }
    body = _event("transaction.completed", purchase_data)
    r = await client.post(WEBHOOK, content=body, headers={"Paddle-Signature": _sign(body)})
    assert r.status_code == 200, r.text
    rows = (await db_session.execute(
        select(CertificationPurchase).where(CertificationPurchase.external_ref == "txn_01refund")
    )).scalars().all()
    assert len(rows) == 1

    refund = {"action": "refund", "status": "approved", "transaction_id": "txn_01refund"}
    body = _event("adjustment.created", refund)
    r = await client.post(WEBHOOK, content=body, headers={"Paddle-Signature": _sign(body)})
    assert r.status_code == 200, r.text

    rows = (await db_session.execute(
        select(CertificationPurchase).where(CertificationPurchase.external_ref == "txn_01refund")
    )).scalars().all()
    assert rows == []


@pytest.mark.asyncio
async def test_a_pending_refund_does_not_revoke_anything_yet(client, db_session, user) -> None:
    db_session.add(Track(id="trkCERT4", name_es="C", name_en="C", order=93, is_certification=True))
    await db_session.commit()
    purchase_data = {
        "id": "txn_01pending", "status": "completed", "subscription_id": None,
        "items": [{"price": {"id": CERT}}],
        "custom_data": {"user_id": str(user.id), "track_id": "trkCERT4"},
    }
    body = _event("transaction.completed", purchase_data)
    await client.post(WEBHOOK, content=body, headers={"Paddle-Signature": _sign(body)})

    pending = {"action": "refund", "status": "pending_approval", "transaction_id": "txn_01pending"}
    body = _event("adjustment.created", pending)
    r = await client.post(WEBHOOK, content=body, headers={"Paddle-Signature": _sign(body)})
    assert r.status_code == 200

    credit = {"action": "credit", "status": "approved", "transaction_id": "txn_01pending"}
    body = _event("adjustment.created", credit)
    r = await client.post(WEBHOOK, content=body, headers={"Paddle-Signature": _sign(body)})
    assert r.status_code == 200

    rows = (await db_session.execute(
        select(CertificationPurchase).where(CertificationPurchase.external_ref == "txn_01pending")
    )).scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_a_refund_for_an_unknown_transaction_is_a_no_op(client) -> None:
    body = _event("adjustment.created", {"action": "refund", "status": "approved", "transaction_id": "txn_ghost"})
    r = await client.post(WEBHOOK, content=body, headers={"Paddle-Signature": _sign(body)})
    assert r.status_code == 200


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
    monkeypatch.setattr(settings, "CERTIFICATION_PAYWALL", True)
    cfg = (await client.get("/api/v1/billing/paddle/config")).json()
    assert cfg["enabled"] is True and cfg["environment"] == "production"
    assert cfg["prices"] == {
        "plus": PLUS, "pro": PRO, "certification": CERT, "plus_annual": None, "pro_annual": None,
    }


@pytest.mark.asyncio
async def test_annual_prices_only_appear_behind_their_flag(client, monkeypatch) -> None:
    """40.9: el precio y el reembolso son del dueño — `ANNUAL_PLAN_ENABLED`
    apagado (el default) no debe exponer el id aunque ya esté puesto."""
    monkeypatch.setattr(settings, "PADDLE_PRICE_PLUS_ANNUAL", "pri_plus_annual")
    monkeypatch.setattr(settings, "PADDLE_PRICE_PRO_ANNUAL", "pri_pro_annual")

    off = (await client.get("/api/v1/billing/paddle/config")).json()
    assert off["prices"]["plus_annual"] is None and off["prices"]["pro_annual"] is None

    monkeypatch.setattr(settings, "ANNUAL_PLAN_ENABLED", True)
    on = (await client.get("/api/v1/billing/paddle/config")).json()
    assert on["prices"]["plus_annual"] == "pri_plus_annual"
    assert on["prices"]["pro_annual"] == "pri_pro_annual"


@pytest.mark.asyncio
async def test_certification_price_only_appears_behind_the_paywall(client, monkeypatch) -> None:
    """Auditoría de pantallas, 2026-10-15: con `CERTIFICATION_PAYWALL` apagado
    el examen certificador es gratis, así que `/checkout?plan=certification`
    no puede cobrarlo aunque el id de Paddle ya esté puesto. Sin precio, la
    pantalla de pago dice «no disponible» (CheckoutScreen)."""
    monkeypatch.setattr(settings, "CERTIFICATION_PAYWALL", False)
    off = (await client.get("/api/v1/billing/paddle/config")).json()
    assert off["prices"]["certification"] is None

    monkeypatch.setattr(settings, "CERTIFICATION_PAYWALL", True)
    on = (await client.get("/api/v1/billing/paddle/config")).json()
    assert on["prices"]["certification"] == CERT


def test_annual_price_grants_the_same_tier_as_monthly(user, monkeypatch) -> None:
    """Un `subscription.created` con el precio anual tiene que dar acceso
    igual que el mensual — el periodo lo lleva Paddle, no esta tabla."""
    with_annual = _sub(user.id, price="pri_plus_annual")
    assert not paddle_billing.apply_subscription_event(user, "subscription.created", with_annual)
    assert user.subscription_tier is None  # el id anual no estaba configurado: sin mapear, no hace nada

    monkeypatch.setattr(settings, "PADDLE_PRICE_PLUS_ANNUAL", "pri_plus_annual")
    assert paddle_billing.apply_subscription_event(user, "subscription.created", with_annual)
    assert user.subscription_tier == "plus" and user_meets_tier(user, "plus")


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


# ── Cancelar desde la app ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cancel_endpoint_asks_paddle_for_the_users_subscription(
    client, db_session, user, auth_headers, monkeypatch
) -> None:
    calls: list[str] = []

    async def fake_cancel(sub_id: str, *, immediately: bool = False) -> bool:
        calls.append(f"{sub_id}:{immediately}")
        return True

    monkeypatch.setattr(paddle_billing, "cancel_subscription", fake_cancel)
    user.subscription_provider = "paddle"
    user.paddle_subscription_id = "sub_01mine"
    await db_session.commit()

    r = await client.post("/api/v1/billing/paddle/cancel", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["cancel_requested"] is True
    # Al final del periodo pagado, nunca de inmediato: es lo que dicen los Términos.
    assert calls == ["sub_01mine:False"]


@pytest.mark.asyncio
async def test_cancel_endpoint_without_paddle_subscription_is_404(client, auth_headers, monkeypatch) -> None:
    async def boom(*a, **k):
        raise AssertionError("no debía llamar a Paddle")

    monkeypatch.setattr(paddle_billing, "cancel_subscription", boom)
    r = await client.post("/api/v1/billing/paddle/cancel", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_cancel_endpoint_reports_a_paddle_refusal(client, db_session, user, auth_headers, monkeypatch) -> None:
    async def refuse(*a, **k) -> bool:
        return False

    monkeypatch.setattr(paddle_billing, "cancel_subscription", refuse)
    user.subscription_provider = "paddle"
    user.paddle_subscription_id = "sub_01mine"
    await db_session.commit()
    r = await client.post("/api/v1/billing/paddle/cancel", headers=auth_headers)
    assert r.status_code == 502


# ── D-10 (dueño, 2026-10-12): entrega al menos una vez, sin orden ─────────────


async def _post(client, body: bytes):
    return await client.post(WEBHOOK, content=body, headers={"Paddle-Signature": _sign(body)})


@pytest.mark.asyncio
async def test_a_redelivered_event_is_applied_only_once(client, db_session, user) -> None:
    """El mismo `event_id` dos veces: la segunda no vuelve a aplicar nada."""
    created = _event("subscription.created", _sub(user.id), event_id="evt_dup")
    assert (await _post(client, created)).status_code == 200
    # Entre las dos entregas el alumno cancela (otro evento, posterior).
    cancel = _event(
        "subscription.canceled",
        _sub(user.id, status="canceled", canceled_at=datetime.now(UTC).isoformat()),
    )
    assert (await _post(client, cancel)).status_code == 200
    # Paddle reintenta el `created` original: no puede devolver el plan.
    assert (await _post(client, created)).status_code == 200

    await db_session.refresh(user)
    assert user.is_premium is False
    assert (await db_session.scalar(select(func.count()).select_from(PaddleEvent))) == 2


@pytest.mark.asyncio
async def test_an_older_update_after_the_cancel_does_not_restore_the_plan(
    client, db_session, user
) -> None:
    """Paddle no garantiza el orden: un `subscription.updated` (active) que se
    generó antes del `canceled` de la MISMA suscripción y llega después no
    devuelve el plan."""
    now = datetime.now(UTC)
    created = _event("subscription.created", _sub(user.id), occurred_at=now - timedelta(minutes=10))
    cancel = _event(
        "subscription.canceled",
        _sub(user.id, status="canceled", canceled_at=now.isoformat()),
        occurred_at=now,
    )
    late_update = _event(
        "subscription.updated", _sub(user.id), occurred_at=now - timedelta(minutes=5)
    )
    for body in (created, cancel, late_update):
        assert (await _post(client, body)).status_code == 200

    await db_session.refresh(user)
    assert user.is_premium is False
    assert user.subscription_status == "canceled"


@pytest.mark.asyncio
async def test_a_newer_update_still_applies(client, db_session, user) -> None:
    """La guarda de orden no congela la suscripción: un evento posterior sí cuenta."""
    now = datetime.now(UTC)
    cancel = _event(
        "subscription.canceled",
        _sub(user.id, status="canceled", canceled_at=now.isoformat()),
        occurred_at=now - timedelta(minutes=5),
    )
    reactivated = _event("subscription.updated", _sub(user.id), occurred_at=now)
    for body in (cancel, reactivated):
        assert (await _post(client, body)).status_code == 200
    await db_session.refresh(user)
    assert user.is_premium is True


@pytest.mark.asyncio
async def test_a_duplicate_certification_purchase_event_grants_once(
    client, db_session, user
) -> None:
    db_session.add(Track(id="trkDUP", name_es="C", name_en="C", order=95, is_certification=True))
    await db_session.commit()
    data = {
        "id": "txn_01dup", "status": "completed", "subscription_id": None,
        "items": [{"price": {"id": CERT}}],
        "custom_data": {"user_id": str(user.id), "track_id": "trkDUP"},
    }
    body = _event("transaction.completed", data, event_id="evt_txn_dup")
    for _ in range(2):
        assert (await _post(client, body)).status_code == 200
    rows = (await db_session.execute(
        select(CertificationPurchase).where(CertificationPurchase.external_ref == "txn_01dup")
    )).scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_a_full_refund_of_a_subscription_charge_removes_the_plan(
    client, db_session, user
) -> None:
    """Reembolso completo de un cobro de suscripción: el plan cae en el acto
    (antes solo se miraban las compras de certificación)."""
    assert (await _post(client, _event("subscription.created", _sub(user.id)))).status_code == 200
    await db_session.refresh(user)
    assert user.is_premium is True

    refund = {
        "action": "refund", "type": "full", "status": "approved",
        "transaction_id": "txn_01subcharge", "subscription_id": "sub_01test",
    }
    assert (await _post(client, _event("adjustment.created", refund))).status_code == 200
    await db_session.refresh(user)
    assert user.is_premium is False
    assert user.subscription_status == "canceled"


@pytest.mark.asyncio
async def test_a_partial_refund_of_a_subscription_keeps_the_plan(client, db_session, user) -> None:
    assert (await _post(client, _event("subscription.created", _sub(user.id)))).status_code == 200
    refund = {
        "action": "refund", "type": "partial", "status": "approved",
        "transaction_id": "txn_01subcharge", "subscription_id": "sub_01test",
    }
    assert (await _post(client, _event("adjustment.created", refund))).status_code == 200
    await db_session.refresh(user)
    assert user.is_premium is True


@pytest.mark.asyncio
async def test_a_refund_of_someone_elses_subscription_touches_nobody(
    client, db_session, user
) -> None:
    assert (await _post(client, _event("subscription.created", _sub(user.id)))).status_code == 200
    refund = {
        "action": "refund", "type": "full", "status": "approved",
        "transaction_id": "txn_01other", "subscription_id": "sub_01someone_else",
    }
    assert (await _post(client, _event("adjustment.created", refund))).status_code == 200
    await db_session.refresh(user)
    assert user.is_premium is True


@pytest.mark.asyncio
async def test_a_failed_event_is_not_recorded_so_paddle_can_retry(
    client, db_session, user, monkeypatch
) -> None:
    """Si aplicar el evento falla, no queda fila: el reintento lo vuelve a aplicar."""
    calls = {"n": 0}
    real = paddle_billing.apply_subscription_event

    def flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        return real(*args, **kwargs)

    monkeypatch.setattr(paddle_billing, "apply_subscription_event", flaky)
    body = _event("subscription.created", _sub(user.id), event_id="evt_retry")
    assert (await _post(client, body)).status_code == 500
    assert (await db_session.get(PaddleEvent, "evt_retry")) is None
    assert (await _post(client, body)).status_code == 200
    await db_session.refresh(user)
    assert user.is_premium is True


@pytest.mark.asyncio
async def test_a_redelivered_purchase_after_its_refund_does_not_grant_again(
    client, db_session, user
) -> None:
    """Sin deduplicación, este es el caso que cuesta dinero: compra, reembolso y
    Paddle reentrega la compra. No hay guarda de orden para transacciones, así
    que solo el `event_id` impide devolver el examen a quien ya cobró el reembolso."""
    db_session.add(Track(id="trkREDO", name_es="C", name_en="C", order=96, is_certification=True))
    await db_session.commit()
    data = {
        "id": "txn_01redo", "status": "completed", "subscription_id": None,
        "items": [{"price": {"id": CERT}}],
        "custom_data": {"user_id": str(user.id), "track_id": "trkREDO"},
    }
    purchase = _event("transaction.completed", data, event_id="evt_purchase_redo")
    assert (await _post(client, purchase)).status_code == 200
    refund = {"action": "refund", "type": "full", "status": "approved", "transaction_id": "txn_01redo"}
    assert (await _post(client, _event("adjustment.created", refund))).status_code == 200
    assert (await _post(client, purchase)).status_code == 200

    rows = (await db_session.execute(
        select(CertificationPurchase).where(CertificationPurchase.external_ref == "txn_01redo")
    )).scalars().all()
    assert rows == []
