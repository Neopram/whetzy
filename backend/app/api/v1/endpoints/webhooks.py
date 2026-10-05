"""Paddle webhook endpoints: Paddle Billing (pago web, H.29) y pagos a instructores (28.7)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.instructor import InstructorPayout
from app.models.user import User
from app.services import analytics, paddle_billing
from app.services import certification as certification_service

logger = logging.getLogger(__name__)
router = APIRouter()

async def handle_payout_completed(
    event_data: dict[str, Any],
    db: AsyncSession,
) -> None:
    """Handle payout.completed webhook.
    
    Mark instructor payout as completed.
    """
    payout_id = event_data.get("payout_id")
    instructor_id = event_data.get("instructor_id")
    amount_cents = event_data.get("amount_cents")
    payout_date = event_data.get("payout_date")

    if not payout_id or not instructor_id:
        logger.warning("Missing payout_id or instructor_id in payout.completed")
        return

    # Find payout by ID (assume event includes our payout ID)
    payout = await db.scalar(
        select(InstructorPayout).where(
            InstructorPayout.instructor_id == instructor_id,
            InstructorPayout.status == "processing",
        )
    )

    if not payout:
        logger.warning("No processing payout found for instructor %s", instructor_id)
        return

    # Update payout status
    payout.status = "completed"
    payout.payout_date = datetime.fromisoformat(payout_date) if payout_date else datetime.now(UTC)
    await db.commit()

    logger.info(
        "Payout %s for instructor %s marked completed (€%.2f)",
        payout.id,
        instructor_id,
        (amount_cents or 0) / 100,
    )


@router.post("/paddle", status_code=status.HTTP_200_OK)
async def webhook_paddle(request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, bool]:
    """Receptor de Paddle Billing (pago web, H.29).

    Firma `Paddle-Signature` verificada en `paddle_billing.verify_webhook`.
    Si procesar falla se responde 500 para que Paddle reintente: aplicar un
    evento es idempotente (escribe el estado, no suma), así que un reintento
    no duplica nada, y tragarse el error dejaba a un alumno que pagó sin plan.
    """
    body = await request.body()
    try:
        event = paddle_billing.verify_webhook(body, request.headers.get("Paddle-Signature"))
    except RuntimeError as exc:
        logger.error("Paddle webhook recibido sin PADDLE_WEBHOOK_SECRET configurado")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        logger.warning("Paddle webhook rechazado: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature") from exc

    event_type = str(event.get("event_type", ""))
    data: dict[str, Any] = event["data"]
    logger.info("Paddle webhook: type=%s id=%s", event_type, event.get("event_id"))

    try:
        if event_type.startswith("subscription."):
            await _apply_subscription(db, event_type, data)
        elif event_type == "transaction.completed":
            await _apply_transaction(db, data)
        elif event_type in ("adjustment.created", "adjustment.updated"):
            await _apply_refund(db, data)
        elif event_type == "payout.completed":
            await handle_payout_completed(data, db)
    except Exception as exc:
        logger.exception("Error procesando el webhook de Paddle %s", event.get("event_id"))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="processing error") from exc
    return {"received": True}


async def _apply_subscription(db: AsyncSession, event_type: str, data: dict[str, Any]) -> None:
    user_id = paddle_billing.resolve_user_id(data)
    user = await db.get(User, user_id) if user_id else None
    if user is None:
        # Sin `custom_data.user_id` (o de un usuario que no existe) no hay a
        # quién dar el plan; reintentar no lo arregla.
        logger.warning("Paddle %s sin usuario resoluble (sub=%s)", event_type, data.get("id"))
        return
    was_premium = user.is_premium
    if paddle_billing.apply_subscription_event(user, event_type, data):
        paddle_billing.record_withdrawal_waiver(user, data)
        if user.is_premium and not was_premium:
            # Mismo evento que los webhooks de Stripe y RevenueCat (37.20): solo
            # en la transición real gratis → pago, nunca en una renovación.
            await analytics.track(db, "subscription_started", user_id=user.id)
        await db.commit()


async def _apply_transaction(db: AsyncSession, data: dict[str, Any]) -> None:
    purchase = paddle_billing.certification_purchase(data)
    if purchase is None:
        return
    user_id, track_id, txn_id = purchase
    user = await db.get(User, user_id)
    if user is None:
        logger.warning("Paddle certificación de usuario inexistente %s (txn=%s)", user_id, txn_id)
        return
    await certification_service.grant(db, user_id, track_id, source="paddle", external_ref=txn_id)
    paddle_billing.record_withdrawal_waiver(user, data)
    await db.commit()


async def _apply_refund(db: AsyncSession, data: dict[str, Any]) -> None:
    """`adjustment.created`/`adjustment.updated`: retira lo que ese cargo dio.

    Paddle Billing manda los reembolsos como `adjustment`, no como un
    `transaction.refunded` (developer.paddle.com/webhooks/adjustments,
    verificado 2026-10-04): `action` distingue reembolso de crédito o
    contracargo, y `status` si Paddle ya lo aprobó. Antes de esto nada
    escuchaba estos eventos: un alumno reembolsado conservaba el derecho al
    examen certificador para siempre.

    Solo `action == "refund"` con `status == "approved"`; un crédito, un
    contracargo o un reembolso todavía pendiente/rechazado no tocan nada
    (cada uno necesitaría su propia regla, que no es la que pide esta tarea).
    """
    if data.get("action") != "refund" or data.get("status") != "approved":
        return
    txn_id = data.get("transaction_id")
    if not txn_id:
        logger.warning("Paddle adjustment.refund sin transaction_id")
        return
    revoked = await certification_service.revoke_purchase_by_external_ref(db, str(txn_id))
    if revoked:
        await db.commit()
        logger.info("Certificación revocada por reembolso Paddle txn=%s", txn_id)
