"""Web Push notification delivery (3.3).

Uses pywebpush + VAPID (RFC 8292) to send push messages to browser endpoints.

Patching: tests can patch ``app.services.push_service.webpush`` to avoid
making real HTTP calls to browser push services.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)

# `webpush()` es una llamada bloqueante (requests) y, sin `timeout`, pywebpush
# no pone ninguno por su cuenta -- un endpoint que no responde podía colgar
# la petición indefinidamente. 10 s, igual que el SMTP de `email.py`.
_WEBPUSH_TIMEOUT_SECONDS = 10.0

try:
    from pywebpush import WebPushException
    from pywebpush import webpush as _webpush

    webpush = _webpush
    WebPushEx = WebPushException
except ImportError:
    webpush = None
    WebPushEx = Exception


def is_configured() -> bool:
    return bool(settings.VAPID_PRIVATE_KEY and settings.VAPID_PUBLIC_KEY)


def localize(lang: str | None, es: str, en: str) -> str:
    """Pick the ES or EN copy of a push notification string (23.1).

    Same fallback rule as ``email._render``: anything that isn't literally
    ``"en"`` gets Spanish, never a silent English default regardless of the
    recipient's actual language.
    """
    return en if lang == "en" else es


async def send_to_user(
    db: AsyncSession,
    user_id: object,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
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

    async def _send_one(sub: PushSubscription) -> Exception | None:
        try:
            await asyncio.to_thread(
                webpush,
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={
                    "sub": settings.VAPID_EMAIL,
                },
                timeout=_WEBPUSH_TIMEOUT_SECONDS,
            )
            return None
        except Exception as exc:  # noqa: BLE001
            return exc

    # Cada envío a su propio hilo y los de este usuario en paralelo, no uno
    # detrás de otro: antes, un endpoint lento bloqueaba el bucle de eventos
    # (como el SMTP de `email.py` antes de despacharse a un hilo) y además
    # retrasaba en cadena al resto de dispositivos de este mismo usuario.
    results = await asyncio.gather(*(_send_one(sub) for sub in subs))

    sent = 0
    gone_ids = []
    for sub, exc in zip(subs, results, strict=True):
        if exc is None:
            sent += 1
            continue
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
