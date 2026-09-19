"""Paddle webhook endpoints (28.7: monthly payouts, subscription events)."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.services.economy import CreditsService
from app.models.instructor import InstructorPayout
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

# Plan to credits mapping (plan_id -> monthly credits)
PLAN_CREDITS_MAP = {
    "pro_monthly": 3000,
    "plus_monthly": 1500,
}


def verify_paddle_signature(signature: str, body: bytes) -> bool:
    """Verify Paddle webhook signature using X-Signature header.
    
    Paddle uses HMAC-SHA256 of the body with the API key.
    """
    if not settings.PADDLE_API_KEY:
        # Fallaba ABIERTO: sin clave configurada daba por buena cualquier firma.
        # Este endpoint esta publicado en produccion y concede creditos, asi que
        # con la clave sin poner —que es como esta hasta que Paddle este de
        # alta— cualquiera que supiera la URL podia regalarse saldo. Sin clave
        # no hay nada que verificar, y lo que no se puede verificar se rechaza.
        logger.error(
            "PADDLE_API_KEY sin configurar: se rechaza el webhook en vez de "
            "aceptarlo sin verificar"
        )
        return False

    expected_signature = hmac.new(
        settings.PADDLE_API_KEY.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


async def handle_subscription_created(
    event_data: dict[str, Any],
    db: AsyncSession,
) -> None:
    """Handle subscription.created webhook.
    
    Grant credits to user based on plan_id.
    """
    raw_user_id = event_data.get("user_id")
    plan_id = event_data.get("plan_id")
    try:
        user_id = uuid.UUID(str(raw_user_id)) if raw_user_id else None
    except ValueError:
        logger.warning("user_id no es un UUID valido: %r", raw_user_id)
        return
    subscription_id = event_data.get("subscription_id")

    if not user_id or not plan_id:
        logger.warning("Missing user_id or plan_id in subscription.created")
        return

    # Check user exists
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        logger.warning("User %s not found for subscription %s", user_id, subscription_id)
        return

    # Get credits for this plan
    credits = PLAN_CREDITS_MAP.get(plan_id, 0)
    if not credits:
        logger.info("No credit mapping for plan %s", plan_id)
        return

    # El saldo ya no se guarda por fila: `grant_credits` abre un lote con su
    # clave de idempotencia, asi que si Paddle reintenta el webhook —y reintenta—
    # el credito no se concede dos veces.
    await CreditsService.grant_credits(
        db,
        user_id=user_id,
        amount=credits,
        reason=f"subscription_created:{plan_id}",
        ref_type="paddle_subscription",
        ref_id=subscription_id,
    )
    await db.commit()
    logger.info(
        "Granted %d credits to user %s (plan %s, subscription %s)",
        credits,
        user_id,
        plan_id,
        subscription_id,
    )


async def handle_subscription_updated(
    event_data: dict[str, Any],
    db: AsyncSession,
) -> None:
    """Handle subscription.updated webhook.
    
    Track plan changes (no action for now, future: handle plan downgrades).
    """
    user_id = event_data.get("user_id")
    old_plan = event_data.get("old_plan_id")
    new_plan = event_data.get("plan_id")
    subscription_id = event_data.get("subscription_id")

    logger.info(
        "Subscription updated for user %s: %s -> %s (subscription %s)",
        user_id,
        old_plan,
        new_plan,
        subscription_id,
    )


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
    """Paddle webhook receiver.
    
    Handles: subscription.created, subscription.updated, payout.completed
    Verifies X-Signature header and logs audit trail.
    """
# Get signature header
    signature = request.headers.get("X-Signature")
    if not signature:
        logger.warning("Missing X-Signature header in Paddle webhook")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature",
        )

    # Read body
    body = await request.body()

    # Verify signature
    if not verify_paddle_signature(signature, body):
        logger.warning("Invalid Paddle webhook signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    # Parse event
    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in Paddle webhook")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON",
        )

    event_type = event.get("event_type", "unknown")
    event_data = event.get("data", {})
    webhook_id = event.get("webhook_id")

    logger.info("Received Paddle webhook: type=%s id=%s", event_type, webhook_id)

    try:
        # Dispatch to handler based on event type
        if event_type == "subscription.created":
            await handle_subscription_created(event_data, db)
        elif event_type == "subscription.updated":
            await handle_subscription_updated(event_data, db)
        elif event_type == "payout.completed":
            await handle_payout_completed(event_data, db)
        else:
            logger.debug("Unhandled webhook event type: %s", event_type)

    except Exception:
        logger.exception("Error processing Paddle webhook %s", webhook_id)
        # Don't fail the webhook response; return 200 so Paddle doesn't retry
        # (failed retries would lock up the queue)

    return {"received": True}


