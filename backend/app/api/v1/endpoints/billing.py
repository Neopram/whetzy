"""Billing endpoints: Stripe checkout + webhook + subscription status (7.2, 21.4)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services import analytics, paddle_billing, revenuecat_service, stripe_service

logger = logging.getLogger(__name__)
router = APIRouter()


class CheckoutRequest(BaseModel):
    price_id: str  # Stripe price ID, e.g. settings.STRIPE_PRICE_PLUS
    eu_withdrawal_waiver: bool = False


class CheckoutResponse(BaseModel):
    checkout_url: str


class SubscriptionResponse(BaseModel):
    is_premium: bool
    subscription_status: str | None
    subscription_tier: str | None
    subscription_provider: str | None  # "stripe" | "revenuecat" | "paddle" | None (17.14, H.29)
    stripe_customer_id: str | None
    stripe_subscription_id: str | None


@router.get("/paddle/config", status_code=status.HTTP_200_OK)
async def paddle_config() -> dict[str, Any]:
    """Lo que necesita la web para abrir el checkout de Paddle.js (H.29).

    Público a propósito: el token de cliente y los ids de precio están hechos
    para ir en el navegador. `enabled` es False hasta que el dueño los configure.
    """
    return paddle_billing.public_config()


@router.post("/paddle/cancel", status_code=status.HTTP_200_OK)
async def paddle_cancel(user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Cancela la suscripción de Paddle al final del periodo pagado (H.29).

    Lo que prometen los Términos: cancelar en cualquier momento y conservar el
    acceso hasta el final del periodo facturado. Aquí solo se pide a Paddle; el
    estado lo escribe el webhook (`subscription.updated` con
    `scheduled_change.action = "cancel"`), igual que si se cancelara desde Paddle.
    """
    if user.subscription_provider != "paddle" or not user.paddle_subscription_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no_paddle_subscription")
    if not await paddle_billing.cancel_subscription(user.paddle_subscription_id):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="paddle_cancel_failed")
    return {"cancel_requested": True, "access_until": user.subscription_expires_at}


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_200_OK)
async def create_checkout(
    body: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CheckoutResponse:
    """Create a Stripe checkout session and return the hosted checkout URL."""
    if body.eu_withdrawal_waiver:
        user.eu_withdrawal_waiver_at = datetime.now(UTC)

    try:
        url = stripe_service.create_checkout_session(user, body.price_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:  # stripe.error.*
        logger.exception("Stripe checkout error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Stripe error") from exc

    await db.commit()
    await db.refresh(user)
    return CheckoutResponse(checkout_url=url)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str | None = Header(None, alias="stripe-signature"),
) -> dict[str, Any]:
    """Receive and process Stripe webhook events.

    Stripe calls this endpoint directly; authentication is by signature
    verification (STRIPE_WEBHOOK_SECRET), not by JWT.
    """
    payload = await request.body()
    if not stripe_signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Stripe-Signature header")

    try:
        event = stripe_service.verify_webhook(payload, stripe_signature)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        logger.warning("Stripe webhook signature invalid: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature") from exc

    event_type: str = event["type"]
    logger.info("Stripe webhook received: %s", event_type)

    if event_type in (
        "checkout.session.completed",
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        data_obj = event["data"]["object"]
        customer_id: str | None = data_obj.get("customer")
        if not customer_id:
            return {"received": True}

        result = await db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        user = result.scalars().first()
        if not user:
            logger.warning("Stripe webhook: no user found for customer %s", customer_id)
            return {"received": True}

        # 37.20 (ADR-53 §8): conversion-to-paid rate needs the moment a user
        # first becomes premium, and current state alone can't reconstruct
        # that (a later churn erases it). Comparing before/after here, not
        # inside apply_subscription_event, catches only the real transition —
        # a renewal or tier change while already premium must not re-fire it.
        was_premium = user.is_premium
        stripe_service.apply_subscription_event(user, event)
        if user.is_premium and not was_premium:
            await analytics.track(db, "subscription_started", user_id=user.id)
        await db.commit()

    return {"received": True}


@router.post("/revenuecat/webhook", status_code=status.HTTP_200_OK)
async def revenuecat_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    """Receive and process RevenueCat webhook events (17.14 — mobile IAP).

    RevenueCat calls this directly; authentication is the shared-secret
    Authorization header configured in its dashboard, not a JWT — same
    pattern as /billing/webhook's Stripe signature, different mechanism.
    Off (503) until REVENUECAT_WEBHOOK_AUTHORIZATION is set — sandbox/dev
    only until the owner activates live App Store/Play Store keys (H.2, H.3).
    """
    payload = await request.body()

    try:
        event = revenuecat_service.verify_webhook(payload, authorization)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        logger.warning("RevenueCat webhook rejected: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    event_type = event.get("type", "")
    logger.info("RevenueCat webhook received: %s", event_type)

    user_id = revenuecat_service.resolve_user_id(event)
    if user_id is None:
        return {"received": True}

    user = await db.get(User, user_id)
    if not user:
        logger.warning("RevenueCat webhook: no user found for app_user_id %s", user_id)
        return {"received": True}

    was_premium = user.is_premium
    revenuecat_service.apply_subscription_event(user, event)
    if user.is_premium and not was_premium:
        await analytics.track(db, "subscription_started", user_id=user.id)
    await db.commit()

    return {"received": True}


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    """Return the current user's subscription state."""
    return SubscriptionResponse(
        is_premium=user.is_premium,
        subscription_status=user.subscription_status,
        subscription_tier=user.subscription_tier,
        subscription_provider=user.subscription_provider,
        stripe_customer_id=user.stripe_customer_id,
        stripe_subscription_id=user.stripe_subscription_id,
    )
