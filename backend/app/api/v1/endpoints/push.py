"""Web Push subscription management (3.3).

POST /push/subscribe   — store a PushSubscription for the current user
DELETE /push/subscribe — remove a subscription by endpoint
GET  /push/vapid-key   — return the VAPID public key (used by frontend to subscribe)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.push_subscription import PushSubscription
from app.models.user import User

router = APIRouter()


class SubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscribeRequest(BaseModel):
    endpoint: str
    keys: SubscriptionKeys


class PushUnsubscribeRequest(BaseModel):
    endpoint: str


@router.get("/vapid-key")
async def get_vapid_key() -> dict:
    """Return the VAPID public key so the frontend can subscribe."""
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Web Push not configured",
        )
    return {"vapid_public_key": settings.VAPID_PUBLIC_KEY}


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe(
    body: PushSubscribeRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Register a browser push subscription for the current user."""
    existing = (
        await db.scalars(
            select(PushSubscription).where(
                PushSubscription.user_id == user.id,
                PushSubscription.endpoint == body.endpoint,
            )
        )
    ).first()

    if existing:
        existing.p256dh = body.keys.p256dh
        existing.auth = body.keys.auth
    else:
        db.add(
            PushSubscription(
                user_id=user.id,
                endpoint=body.endpoint,
                p256dh=body.keys.p256dh,
                auth=body.keys.auth,
            )
        )
    await db.commit()
    return {"subscribed": True}


@router.delete("/subscribe", status_code=status.HTTP_200_OK)
async def unsubscribe(
    body: PushUnsubscribeRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Remove a push subscription for the current user."""
    result = await db.execute(
        delete(PushSubscription).where(
            PushSubscription.user_id == user.id,
            PushSubscription.endpoint == body.endpoint,
        )
    )
    await db.commit()
    removed = result.rowcount > 0
    return {"unsubscribed": removed}
