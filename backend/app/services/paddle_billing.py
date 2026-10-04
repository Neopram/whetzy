"""Paddle Billing — pago web (H.29; el dueño descartó Stripe el 2026-10-01).

Misma forma que `revenuecat_service.py` y `stripe_service.py`: verificar el
webhook y aplicar el evento sobre las columnas de derecho de acceso que comparten
los tres raíles (`subscription_tier/status/expires_at/provider`, `is_premium`) y
que lee `core/entitlements.user_meets_tier`.

Formato verificado contra la documentación oficial (2026-10-01):
- Firma: cabecera `Paddle-Signature: ts=<unix>;h1=<hex>`, HMAC-SHA256 de
  `"<ts>:<cuerpo crudo>"` con la clave secreta del destino de notificaciones
  (`pdl_ntfset_...`, Developer tools > Notifications), tolerancia de 5 s
  (developer.paddle.com/webhooks/signature-verification).
- Eventos: `{event_id, event_type, occurred_at, notification_id, data}`; la
  suscripción trae `id` (`sub_`), `status`, `items[].price.id`,
  `current_billing_period.{starts_at,ends_at}`, `scheduled_change`,
  `custom_data`, `canceled_at`; la transacción, `id` (`txn_`), `status`,
  `subscription_id`, `custom_data`, `items[].price.id`.
- Cancelar: `POST /subscriptions/{id}/cancel` con `effective_from`
  (`next_billing_period` | `immediately`); base `sandbox-api.paddle.com` o
  `api.paddle.com`.

El alumno se identifica por `custom_data.user_id`, que el checkout de la web
manda al abrir Paddle.js; la certificación, además, por `custom_data.track_id`.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import settings
from app.models.user import User

logger = logging.getLogger("whetzy")

# Estados de Paddle con acceso vigente.
_LIVE_STATUSES = frozenset({"active", "trialing"})


def configured() -> bool:
    return bool(settings.PADDLE_WEBHOOK_SECRET)


def api_base() -> str:
    if settings.PADDLE_ENVIRONMENT == "production":
        return "https://api.paddle.com"
    return "https://sandbox-api.paddle.com"


def _parse_signature(header: str) -> tuple[str, list[str]]:
    ts = ""
    h1: list[str] = []
    for part in header.split(";"):
        key, _, value = part.strip().partition("=")
        if key == "ts":
            ts = value
        elif key == "h1" and value:
            h1.append(value)
    if not ts or not h1:
        raise ValueError("Malformed Paddle-Signature header")
    return ts, h1


def verify_webhook(
    payload: bytes, signature_header: str | None, now: float | None = None
) -> dict[str, Any]:
    """Autentica y parsea un webhook de Paddle.

    `RuntimeError` si el raíl no está configurado; `ValueError` si falta la
    firma, no cuadra, es más vieja que la tolerancia o el cuerpo no es JSON.
    """
    if not configured():
        raise RuntimeError("Paddle not configured: set PADDLE_WEBHOOK_SECRET")
    if not signature_header:
        raise ValueError("Missing Paddle-Signature header")
    ts, candidates = _parse_signature(signature_header)
    try:
        ts_int = int(ts)
    except ValueError as exc:
        raise ValueError("Non-numeric Paddle-Signature timestamp") from exc
    now = time.time() if now is None else now
    if abs(now - ts_int) > settings.PADDLE_WEBHOOK_TOLERANCE_SECONDS:
        raise ValueError("Paddle-Signature timestamp outside tolerance")
    expected = hmac.new(
        settings.PADDLE_WEBHOOK_SECRET.encode(),
        f"{ts}:".encode() + payload,
        hashlib.sha256,
    ).hexdigest()
    # Durante una rotación de clave Paddle puede mandar varias `h1`.
    if not any(hmac.compare_digest(expected, c) for c in candidates):
        raise ValueError("Invalid Paddle-Signature")
    try:
        event = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON body") from exc
    if not isinstance(event, dict) or not isinstance(event.get("data"), dict):
        raise ValueError("Missing 'data' object")  # noqa: TRY004 — dato no confiable, no error de tipos
    return event


def resolve_user_id(data: dict[str, Any]) -> uuid.UUID | None:
    custom = data.get("custom_data") or {}
    raw = custom.get("user_id") if isinstance(custom, dict) else None
    if not raw:
        return None
    try:
        return uuid.UUID(str(raw))
    except ValueError:
        return None


def price_ids(data: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for item in data.get("items") or []:
        price = item.get("price") if isinstance(item, dict) else None
        if isinstance(price, dict) and price.get("id"):
            ids.append(str(price["id"]))
    return ids


def _price_to_tier() -> dict[str, str]:
    m: dict[str, str] = {}
    if settings.PADDLE_PRICE_PLUS:
        m[settings.PADDLE_PRICE_PLUS] = "plus"
    if settings.PADDLE_PRICE_PRO:
        m[settings.PADDLE_PRICE_PRO] = "pro"
    # 40.9: el id anual da el mismo derecho de acceso que el mensual — el
    # periodo lo lleva Paddle (`current_billing_period`), no esta tabla.
    if settings.PADDLE_PRICE_PLUS_ANNUAL:
        m[settings.PADDLE_PRICE_PLUS_ANNUAL] = "plus"
    if settings.PADDLE_PRICE_PRO_ANNUAL:
        m[settings.PADDLE_PRICE_PRO_ANNUAL] = "pro"
    return m


def _parse_ts(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def apply_subscription_event(user: User, event_type: str, data: dict[str, Any]) -> bool:
    """Aplica un `subscription.*` sobre *user*. Devuelve False si lo ignora.

    Se ignora un precio que Whetzy no vende: no se toca al alumno.
    """
    tier_map = _price_to_tier()
    tier = next((tier_map[p] for p in price_ids(data) if p in tier_map), None)
    if tier is None:
        return False

    status = str(data.get("status") or "")
    period_end = _parse_ts((data.get("current_billing_period") or {}).get("ends_at"))
    user.subscription_provider = "paddle"
    if data.get("id"):
        user.paddle_subscription_id = str(data["id"])

    if event_type == "subscription.canceled" or status == "canceled":
        # La suscripción ya terminó: sin acceso desde ahora.
        user.subscription_status = "canceled"
        user.is_premium = False
        user.subscription_expires_at = _parse_ts(data.get("canceled_at")) or datetime.now(UTC)
        return True

    if status == "paused":
        user.subscription_status = "paused"
        user.is_premium = False
        user.subscription_expires_at = datetime.now(UTC)
        return True

    if status in _LIVE_STATUSES or status == "past_due":
        user.subscription_tier = tier
        user.is_premium = True
        if period_end is not None:
            user.subscription_expires_at = period_end
        scheduled = data.get("scheduled_change") or {}
        if isinstance(scheduled, dict) and scheduled.get("action") == "cancel":
            # Cancelada al final del periodo: el acceso sigue hasta `ends_at`
            # (user_meets_tier corta solo al pasar `subscription_expires_at`).
            user.subscription_status = "canceled"
        else:
            # past_due: Paddle reintenta el cobro; el acceso sigue hasta el fin
            # del periodo pagado, igual que en Stripe y RevenueCat.
            user.subscription_status = "active" if status in _LIVE_STATUSES else "past_due"
        return True

    return False


def record_withdrawal_waiver(user: User, data: dict[str, Any]) -> None:
    """Guarda cuándo aceptó el alumno la renuncia al desistimiento (art. 16.m).

    La página `/checkout` no abre el pago sin esa casilla y la manda como
    `custom_data.eu_withdrawal_waiver = "accepted"`. Se guarda la primera vez,
    igual que hacía el checkout de Stripe.
    """
    custom = data.get("custom_data") or {}
    if not isinstance(custom, dict) or custom.get("eu_withdrawal_waiver") != "accepted":
        return
    if user.eu_withdrawal_waiver_at is None:
        user.eu_withdrawal_waiver_at = datetime.now(UTC)


def certification_purchase(data: dict[str, Any]) -> tuple[uuid.UUID, str, str] | None:
    """Si la transacción completada es la certificación, (user_id, track_id, txn_id)."""
    if not settings.PADDLE_PRICE_CERTIFICATION:
        return None
    if settings.PADDLE_PRICE_CERTIFICATION not in price_ids(data):
        return None
    user_id = resolve_user_id(data)
    custom = data.get("custom_data") or {}
    track_id = custom.get("track_id") if isinstance(custom, dict) else None
    txn_id = data.get("id")
    if user_id is None or not track_id or not txn_id:
        return None
    return user_id, str(track_id), str(txn_id)


async def cancel_subscription(subscription_id: str, *, immediately: bool = False) -> bool:
    """Cancela una suscripción en Paddle. Devuelve True si Paddle la aceptó.

    Sin `PADDLE_API_KEY` no hace nada (y lo dice en el log): borrar una cuenta
    no puede fallar porque el raíl de pago no esté dado de alta.
    """
    if not settings.PADDLE_API_KEY:
        logger.warning("paddle_cancel_skipped no PADDLE_API_KEY sub=%s", subscription_id)
        return False
    effective = "immediately" if immediately else "next_billing_period"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{api_base()}/subscriptions/{subscription_id}/cancel",
                headers={"Authorization": f"Bearer {settings.PADDLE_API_KEY}"},
                json={"effective_from": effective},
            )
    except httpx.HTTPError:
        logger.exception("paddle_cancel_failed sub=%s", subscription_id)
        return False
    if resp.status_code >= 400:
        logger.error(
            "paddle_cancel_rejected sub=%s status=%s body=%s",
            subscription_id, resp.status_code, resp.text[:300],
        )
        return False
    return True


def public_config() -> dict[str, Any]:
    """Lo que la web necesita para abrir Paddle.js. Nada de esto es secreto.

    Los precios `_annual` (40.9) solo salen con `ANNUAL_PLAN_ENABLED=true` —
    el precio y el reembolso son decisión del dueño (ADR-41); con el flag
    apagado el frontend no ofrece la opción aunque el id ya esté puesto.
    """
    enabled = bool(settings.PADDLE_CLIENT_TOKEN and (settings.PADDLE_PRICE_PLUS or settings.PADDLE_PRICE_PRO))
    annual = settings.ANNUAL_PLAN_ENABLED
    return {
        "enabled": enabled,
        "environment": "production" if settings.PADDLE_ENVIRONMENT == "production" else "sandbox",
        "client_token": settings.PADDLE_CLIENT_TOKEN or None,
        "prices": {
            "plus": settings.PADDLE_PRICE_PLUS or None,
            "pro": settings.PADDLE_PRICE_PRO or None,
            "certification": settings.PADDLE_PRICE_CERTIFICATION or None,
            "plus_annual": (settings.PADDLE_PRICE_PLUS_ANNUAL or None) if annual else None,
            "pro_annual": (settings.PADDLE_PRICE_PRO_ANNUAL or None) if annual else None,
        },
    }
