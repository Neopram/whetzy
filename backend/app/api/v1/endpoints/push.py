"""Web Push subscription management (3.3) and streak reminders (P.13).

GET  /push/vapid-key          — VAPID public key (for frontend subscribe)
POST /push/subscribe          — register subscription (auth required)
DELETE /push/subscribe        — remove subscription (auth required)
PATCH /push/preferences       — toggle push_streak_enabled (auth required)
POST /push/streak-reminder    — fire reminder to at-risk users (admin key)
"""

from __future__ import annotations

import ipaddress
import logging
from datetime import UTC, datetime
from typing import Any, cast
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.push_subscription import PushSubscription
from app.models.user import User
from app.services import push_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _require_admin(x_admin_key: str | None = Header(None, alias="X-Admin-Key")) -> None:
    if not settings.CONTENT_ADMIN_KEY or x_admin_key != settings.CONTENT_ADMIN_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin key required")


class SubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscribeRequest(BaseModel):
    endpoint: str
    keys: SubscriptionKeys


def _is_valid_push_endpoint(endpoint: str) -> bool:
    """`endpoint` lo manda el navegador, pero nadie comprobaba que fuera uno.

    `send_to_user` hace un POST desde el servidor a este mismo endpoint
    (`push_service.py`): sin validarlo, una cuenta podía registrar
    `http://169.254.169.254/...` (metadata de la nube) o cualquier IP
    interna como "endpoint" y, en el siguiente recordatorio de racha, el
    propio backend hacía la petición SSRF por ella.

    `https` obligatorio y, cuando el host es un literal IP (nunca lo es en
    un endpoint real de FCM/Mozilla/etc, que siempre dan un nombre), se
    rechaza si es privado, loopback, link-local o reservado. Un hostname
    normal no se resuelve aquí (eso abriría DNS rebinding sin arreglarlo
    del todo igual) — el filtro corta el ataque directo con una IP literal.
    """
    try:
        parsed = urlparse(endpoint)
    except ValueError:
        return False
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    try:
        ip = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        return True  # un hostname real, no un literal IP
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


class PushUnsubscribeRequest(BaseModel):
    endpoint: str


@router.get("/vapid-key")
async def get_vapid_key(response: Response) -> dict[str, Any]:
    """Return the VAPID public key so the frontend can subscribe."""
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Web Push not configured",
        )
    response.headers["Cache-Control"] = "public, max-age=86400"
    return {"vapid_public_key": settings.VAPID_PUBLIC_KEY}


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe(
    body: PushSubscribeRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Register a browser push subscription for the current user."""
    if not _is_valid_push_endpoint(body.endpoint):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid push endpoint")

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
        count = await db.scalar(
            select(func.count(PushSubscription.id)).where(PushSubscription.user_id == user.id)
        )
        if (count or 0) >= settings.PUSH_MAX_SUBSCRIPTIONS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many push subscriptions for this user",
            )
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
) -> dict[str, Any]:
    """Remove a push subscription for the current user."""
    result = cast(
        "CursorResult[Any]",
        await db.execute(
            delete(PushSubscription).where(
                PushSubscription.user_id == user.id,
                PushSubscription.endpoint == body.endpoint,
            )
        ),
    )
    await db.commit()
    removed = result.rowcount > 0
    return {"unsubscribed": removed}


class PushPreferencesRequest(BaseModel):
    streak_enabled: bool


@router.patch("/preferences", status_code=status.HTTP_200_OK)
async def update_preferences(
    body: PushPreferencesRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Toggle push_streak_enabled for the current user (opt-out in one tap)."""
    user.push_streak_enabled = body.streak_enabled
    await db.commit()
    return {"push_streak_enabled": user.push_streak_enabled}


@router.post("/streak-reminder", status_code=status.HTTP_200_OK)
async def send_streak_reminders(
    db: AsyncSession = Depends(get_db),
    _admin: None = Depends(_require_admin),
) -> dict[str, Any]:
    """Fire streak-at-risk push notifications to eligible users.

    Eligible = streak > 0, push_streak_enabled=True, no study today,
    not already reminded today. Max STREAK_REMINDER_MAX_PER_DAY per user.
    Returns counts of notified users and total notifications sent.
    """
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Users with active streaks who haven't studied today
    result = await db.scalars(
        select(User).where(
            User.current_streak > 0,
            User.push_streak_enabled.is_(True),
            (User.last_active < today_start) | User.last_active.is_(None),
            (User.last_streak_reminder_at < today_start)
            | User.last_streak_reminder_at.is_(None),
        )
    )
    candidates = result.all()

    notified_users = 0
    total_sent = 0

    for candidate in candidates:
        sent = await push_service.send_to_user(
            db,
            candidate.id,
            title=push_service.localize(candidate.language, "🔥 ¡No pierdas tu racha!", "🔥 Keep your streak alive!"),
            body=push_service.localize(
                candidate.language,
                f"Llevas {candidate.current_streak} días seguidos — ¡estudia algo hoy!",
                f"You have a {candidate.current_streak}-day streak — study something today!",
            ),
            tag="streak-reminder",
        )
        if sent > 0:
            candidate.last_streak_reminder_at = now
            notified_users += 1
            total_sent += sent

    if notified_users:
        await db.commit()

    return {"notified_users": notified_users, "notifications_sent": total_sent}
