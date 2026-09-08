"""Web Push notification delivery (3.3).

Uses pywebpush + VAPID (RFC 8292) to send push messages to browser endpoints.

Patching: tests can patch ``app.services.push_service.webpush`` to avoid
making real HTTP calls to browser push services.
"""

from __future__ import annotations

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)

try:
    from pywebpush import WebPushException, webpush as _webpush

    webpush = _webpush
    WebPushEx = WebPushException
except ImportError:
    webpush = None  # type: ignore[assignment]
    WebPushEx = Exception


def is_configured() -> bool:
    return bool(settings.VAPID_PRIVATE_KEY and settings.VAPID_PUBLIC_KEY)


async def send_to_user(
    db: AsyncSession,
    user_id: object,
    title: str,
    body: str,
    data: dict | None = None,
    *,
    tag: str | None = None,
) -> int:
    """Send a push notification to all subscriptions of *user_id*.

    Returns the number of subscriptions successfully notified.
    Silently removes subscriptions that return 410 Gone (browser unsubscribed).
    """
    if not is_configured():
        logger.debug("Web Push not configured — skipping notification to user %s", user_id)
        return 0

    subs = (
        await db.scalars(
            select(PushSubscription).where(PushSubscription.user_id == user_id)
        )
    ).all()
    if not subs:
        return 0

    payload = json.dumps(
        {"title": title, "body": body, "tag": tag or "whetzy", **(data or {})}
    )
    sent = 0
    gone_ids = []

    for sub in subs:
        try:
            webpush(  # type: ignore[operator]
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={
                    "sub": settings.VAPID_EMAIL,
                },
            )
            sent += 1
        except Exception as exc:  # noqa: BLE001
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code == 410:
                gone_ids.append(sub.id)
                logger.info("Push subscription %s gone (410); removing", sub.id)
            else:
                logger.warning("Push delivery failed for sub %s: %s", sub.id, exc)

    for gid in gone_ids:
        sub_obj = await db.get(PushSubscription, gid)
        if sub_obj:
            await db.delete(sub_obj)
    if gone_ids:
        await db.flush()

    return sent
