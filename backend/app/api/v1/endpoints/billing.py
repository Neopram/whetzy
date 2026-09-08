"""Billing endpoints: Stripe checkout + webhook + subscription status (7.2)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services import stripe_service

logger = logging.getLogger(__name__)
router = APIRouter()


class CheckoutRequest(BaseModel):
    price_id: str  # Stripe price ID, e.g. settings.STRIPE_PRICE_PLUS


class CheckoutResponse(BaseModel):
    checkout_url: str


class SubscriptionResponse(BaseModel):
    is_premium: bool
    subscription_status: str | None
    subscription_tier: str | None
    stripe_customer_id: str | None
    stripe_subscription_id: str | None


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_200_OK)
async def create_checkout(
    body: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CheckoutResponse:
    """Create a Stripe checkout session and return the hosted checkout URL."""
    try:
        url = stripe_service.create_checkout_session(user, body.price_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:  # stripe.error.*
        logger.exception("Stripe checkout error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Stripe error") from exc

    # Persist stripe_customer_id that may have been set during checkout creation
    await db.commit()
    await db.refresh(user)
    return CheckoutResponse(checkout_url=url)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str | None = Header(None, alias="stripe-signature"),
) -> dict:
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

        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        user = result.scalars().first()
        if not user:
            logger.warning("Stripe webhook: no user found for customer %s", customer_id)
            return {"received": True}

        stripe_service.apply_subscription_event(user, event)
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
        stripe_customer_id=user.stripe_customer_id,
        stripe_subscription_id=user.stripe_subscription_id,
    )
