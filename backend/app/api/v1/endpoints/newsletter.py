"""Newsletter: alta pública con doble opt-in vía Resend (ledger 26.10, H.30).

- ``POST /newsletter/subscribe`` — público, sin cuenta de Whetzy. Crea (o
  reactiva) la fila con ``confirmed=False`` y manda el correo de confirmación.
  Responde igual exista ya el email o no, para no filtrar qué direcciones
  están suscritas.
- ``GET  /newsletter/confirm?token=…`` — el enlace del correo: confirma y lo
  dice en una página HTML (mismo estilo que ``email_prefs.unsubscribe_page``,
  sin depender de ninguna ruta de frontend).
- ``GET  /newsletter/unsubscribe?token=…`` y ``POST`` (One-Click, RFC 8058) —
  misma pareja que ``email_prefs``. El token de confirmación se conserva tras
  confirmar para que sirva también de baja (ver ``NewsletterSubscriber``).
"""

from __future__ import annotations

import hashlib
import html
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.newsletter import NewsletterSubscriber
from app.services import email as email_service

router = APIRouter()

_PAGE = """<!doctype html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Whetzy</title>
<style>body{{font-family:system-ui,sans-serif;background:#0D1015;color:#E8ECF1;
display:grid;place-items:center;min-height:100vh;margin:0;padding:16px}}
main{{max-width:28rem}}a{{color:#FF8A5B}}</style></head>
<body><main><h1>{title}</h1><p>{body}</p><p><a href="{home}">{back}</a></p></main></body></html>"""

_TEXT = {
    "confirmed": {
        "es": {
            "title": "¡Suscripción confirmada!",
            "body": "Ya recibirás el newsletter de Whetzy. Puedes darte de baja cuando "
            "quieras desde el enlace de cualquier correo.",
            "back": "Volver a Whetzy",
        },
        "en": {
            "title": "Subscription confirmed!",
            "body": "You'll now get the Whetzy newsletter. You can unsubscribe any time "
            "from the link in any email.",
            "back": "Back to Whetzy",
        },
    },
    "invalid": {
        "es": {
            "title": "Enlace no válido",
            "body": "Este enlace ya se usó o no es correcto. Si querías suscribirte, "
            "vuelve a intentarlo desde whetzy.com.",
            "back": "Volver a Whetzy",
        },
        "en": {
            "title": "Invalid link",
            "body": "This link was already used or isn't valid. If you wanted to "
            "subscribe, try again from whetzy.com.",
            "back": "Back to Whetzy",
        },
    },
    "unsubscribed": {
        "es": {
            "title": "Te has dado de baja",
            "body": "No recibirás más newsletters de Whetzy.",
            "back": "Volver a Whetzy",
        },
        "en": {
            "title": "You're unsubscribed",
            "body": "You won't get any more Whetzy newsletters.",
            "back": "Back to Whetzy",
        },
    },
}


def _page(kind: str, lang: str) -> HTMLResponse:
    from app.core.config import settings

    lang_key = lang if lang in ("es", "en") else "es"
    t = _TEXT[kind][lang_key]
    return HTMLResponse(
        _PAGE.format(
            lang=lang_key,
            title=html.escape(t["title"]),
            body=html.escape(t["body"]),
            back=html.escape(t["back"]),
            home=html.escape(settings.FRONTEND_BASE_URL),
        )
    )


class SubscribeRequest(BaseModel):
    email: EmailStr
    language: str = "es"


@router.post("/subscribe", status_code=status.HTTP_202_ACCEPTED)
async def subscribe(
    body: SubscribeRequest, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    lang = body.language if body.language in ("es", "en") else "es"
    normalized = body.email.strip().lower()

    existing = (
        await db.execute(
            select(NewsletterSubscriber).where(NewsletterSubscriber.email == normalized)
        )
    ).scalar_one_or_none()

    if existing is not None and existing.confirmed and existing.unsubscribed_at is None:
        # Ya suscrito y confirmado: no reenviar correo, misma respuesta que si no existiera.
        return {"status": "pending_confirmation"}

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    if existing is None:
        db.add(NewsletterSubscriber(email=normalized, language=lang, token_hash=token_hash))
    else:
        # Sin confirmar todavía, o se había dado de baja: token nuevo, correo nuevo.
        existing.token_hash = token_hash
        existing.language = lang
        existing.confirmed = False
        existing.confirmed_at = None
        existing.unsubscribed_at = None

    await db.commit()
    email_service.send_newsletter_confirmation(normalized, token, lang)
    return {"status": "pending_confirmation"}


async def _by_token(token: str, db: AsyncSession) -> NewsletterSubscriber | None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return (
        await db.execute(
            select(NewsletterSubscriber).where(NewsletterSubscriber.token_hash == token_hash)
        )
    ).scalar_one_or_none()


@router.get("/confirm", response_class=HTMLResponse)
async def confirm(
    token: str = Query(..., min_length=10), db: AsyncSession = Depends(get_db)
) -> HTMLResponse:
    sub = await _by_token(token, db)
    if sub is None or sub.unsubscribed_at is not None:
        return _page("invalid", "es")
    sub.confirmed = True
    sub.confirmed_at = datetime.now(UTC)
    await db.commit()
    return _page("confirmed", sub.language)


async def _opt_out(token: str, db: AsyncSession) -> NewsletterSubscriber | None:
    sub = await _by_token(token, db)
    if sub is None:
        return None
    sub.unsubscribed_at = datetime.now(UTC)
    await db.commit()
    return sub


@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_page(
    token: str = Query(..., min_length=10), db: AsyncSession = Depends(get_db)
) -> HTMLResponse:
    sub = await _opt_out(token, db)
    if sub is None:
        return _page("invalid", "es")
    return _page("unsubscribed", sub.language)


@router.post("/unsubscribe", status_code=status.HTTP_200_OK)
async def unsubscribe_one_click(
    token: str = Query(..., min_length=10), db: AsyncSession = Depends(get_db)
) -> dict[str, bool]:
    sub = await _opt_out(token, db)
    return {"unsubscribed": sub is not None}
