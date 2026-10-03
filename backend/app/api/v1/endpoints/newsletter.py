"""Newsletter: alta pública con doble opt-in vía Resend (ledger 26.10, H.30).

- ``POST /newsletter/subscribe`` — público, sin cuenta de Whetzy. Crea (o
  reactiva) la fila con ``confirmed=False`` y manda el correo de confirmación.
  Responde igual exista ya el email o no, para no filtrar qué direcciones
  están suscritas. Un resend a la misma dirección respeta una ventana de
  enfriamiento (``_RESEND_COOLDOWN``) — sin ella, repetir la petición es un
  generador de spam hacia cualquier email ajeno (revisión de [S5], PR #94).
- ``GET  /newsletter/confirm``/``unsubscribe`` — el enlace del correo: una
  página con un botón, **sin mutar nada todavía**. Un escáner de enlaces de
  correo corporativo (Microsoft Safe Links, Proofpoint...) sigue cualquier
  ``GET`` de un correo en cuanto llega, antes de que la persona lo abra; si el
  ``GET`` confirmara o diera de baja directamente, el escáner lo haría por
  ella. Solo ``POST`` muta — lo dispara el botón del navegador, o el POST
  automático «One-Click» (RFC 8058) que mandan Gmail/Yahoo.

El token del enlace es un JWT firmado (``create_unsubscribe_token``,
``app/core/security.py`` — el mismo mecanismo que ``email_prefs.py`` usa para
las cuentas con sesión), no un secreto guardado en esta tabla: se recalcula
sobre el ``id`` del suscriptor cada vez que hace falta, sirve tanto para
confirmar como para la baja, y expira solo.
"""

from __future__ import annotations

import html
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import create_unsubscribe_token, verify_token
from app.models.newsletter import NewsletterSubscriber
from app.services import email as email_service

router = APIRouter()

# Ventana mínima entre dos correos de confirmación a la misma dirección.
# Sin esto, cualquiera puede forzar un envío por petición a un email ajeno:
# un script sin este límite agota la cuota de Resend y quema la reputación
# del remitente (revisión de [S5], PR #94).
_RESEND_COOLDOWN = timedelta(minutes=5)

_PAGE = """<!doctype html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Whetzy</title>
<style>body{{font-family:system-ui,sans-serif;background:#0D1015;color:#E8ECF1;
display:grid;place-items:center;min-height:100vh;margin:0;padding:16px}}
main{{max-width:28rem}}a{{color:#FF8A5B}}
button{{background:#6366f1;color:#fff;border:none;padding:10px 20px;border-radius:6px;
font-size:1rem;cursor:pointer}}</style></head>
<body><main><h1>{title}</h1><p>{body}</p>{action}<p><a href="{home}">{back}</a></p></main></body></html>"""

_FORM = """<form method="post" action="{action_url}"><button type="submit">{button}</button></form>"""

_TEXT = {
    "confirm_prompt": {
        "es": {
            "title": "Confirma tu suscripción",
            "body": "Un último paso: confirma que quieres recibir el newsletter de Whetzy.",
            "button": "Confirmar suscripción",
            "back": "Volver a Whetzy",
        },
        "en": {
            "title": "Confirm your subscription",
            "body": "One last step: confirm you want the Whetzy newsletter.",
            "button": "Confirm subscription",
            "back": "Back to Whetzy",
        },
    },
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
    "unsubscribe_prompt": {
        "es": {
            "title": "¿Darte de baja?",
            "body": "Dejarás de recibir el newsletter de Whetzy.",
            "button": "Darte de baja",
            "back": "Volver a Whetzy",
        },
        "en": {
            "title": "Unsubscribe?",
            "body": "You'll stop getting the Whetzy newsletter.",
            "button": "Unsubscribe",
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
    "invalid": {
        "es": {
            "title": "Enlace no válido",
            "body": "Este enlace caducó o no es correcto. Si querías suscribirte, "
            "vuelve a intentarlo desde whetzy.com.",
            "back": "Volver a Whetzy",
        },
        "en": {
            "title": "Invalid link",
            "body": "This link expired or isn't valid. If you wanted to subscribe, "
            "try again from whetzy.com.",
            "back": "Back to Whetzy",
        },
    },
}


def _page(kind: str, lang: str, action_url: str | None = None) -> HTMLResponse:
    from app.core.config import settings

    lang_key = lang if lang in ("es", "en") else "es"
    t = _TEXT[kind][lang_key]
    action = ""
    if action_url is not None:
        action = _FORM.format(action_url=html.escape(action_url), button=html.escape(t["button"]))
    return HTMLResponse(
        _PAGE.format(
            lang=lang_key,
            title=html.escape(t["title"]),
            body=html.escape(t["body"]),
            action=action,
            back=html.escape(t["back"]),
            home=html.escape(settings.FRONTEND_BASE_URL),
        )
    )


class SubscribeRequest(BaseModel):
    email: EmailStr
    language: str = "es"


async def _send_confirmation(
    db: AsyncSession, subscriber: NewsletterSubscriber, email_addr: str, lang: str
) -> None:
    subscriber.language = lang
    subscriber.last_sent_at = datetime.now(UTC)
    await db.commit()
    token = create_unsubscribe_token(subscriber.id)
    email_service.send_newsletter_confirmation(email_addr, token, lang)


@router.post("/subscribe", status_code=status.HTTP_202_ACCEPTED)
async def subscribe(
    body: SubscribeRequest, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    lang = body.language if body.language in ("es", "en") else "es"
    normalized = body.email.strip().lower()
    now = datetime.now(UTC)

    existing = (
        await db.execute(
            select(NewsletterSubscriber).where(NewsletterSubscriber.email == normalized)
        )
    ).scalar_one_or_none()

    if existing is None:
        new_subscriber = NewsletterSubscriber(email=normalized, language=lang)
        db.add(new_subscriber)
        try:
            await db.flush()
        except IntegrityError:
            # Alta concurrente de la misma dirección entre el SELECT y el INSERT:
            # la fila ya existe, se trata como si hubiera salido ahí.
            await db.rollback()
            existing = (
                await db.execute(
                    select(NewsletterSubscriber).where(NewsletterSubscriber.email == normalized)
                )
            ).scalar_one_or_none()
            if existing is None:
                raise
        else:
            await _send_confirmation(db, new_subscriber, normalized, lang)
            return {"status": "pending_confirmation"}

    if existing.confirmed and existing.unsubscribed_at is None:
        # Ya suscrito y confirmado: no reenviar correo, misma respuesta que si no existiera.
        return {"status": "pending_confirmation"}

    last_sent = existing.last_sent_at
    if last_sent is not None:
        # Postgres devuelve TIMESTAMPTZ aware; SQLite (la suite de tests) lo
        # devuelve naive — mismo motivo que `_as_utc` en app/core/security.py.
        if last_sent.tzinfo is None:
            last_sent = last_sent.replace(tzinfo=UTC)
        if now - last_sent < _RESEND_COOLDOWN:
            # Dentro de la ventana de enfriamiento: ni correo ni cambio de estado.
            return {"status": "pending_confirmation"}

    existing.confirmed = False
    existing.confirmed_at = None
    existing.unsubscribed_at = None
    await _send_confirmation(db, existing, normalized, lang)
    return {"status": "pending_confirmation"}


def _token_subscriber_id(token: str) -> uuid.UUID | None:
    try:
        payload = verify_token(token, expected_type="unsubscribe")
        return uuid.UUID(str(payload.sub))
    except (HTTPException, ValueError):
        return None


async def _lookup(token: str, db: AsyncSession) -> NewsletterSubscriber | None:
    subscriber_id = _token_subscriber_id(token)
    if subscriber_id is None:
        return None
    return await db.get(NewsletterSubscriber, subscriber_id)


@router.get("/confirm", response_class=HTMLResponse)
async def confirm_prompt(
    token: str = Query(..., min_length=10),
    lang: str = Query("es"),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    sub = await _lookup(token, db)
    if sub is None or sub.unsubscribed_at is not None:
        return _page("invalid", lang)
    if sub.confirmed:
        return _page("confirmed", sub.language)
    return _page("confirm_prompt", sub.language, action_url=f"/api/v1/newsletter/confirm?token={token}")


@router.post("/confirm", response_class=HTMLResponse)
async def confirm(
    token: str = Query(..., min_length=10),
    lang: str = Query("es"),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    sub = await _lookup(token, db)
    if sub is None or sub.unsubscribed_at is not None:
        return _page("invalid", lang)
    if not sub.confirmed:
        sub.confirmed = True
        sub.confirmed_at = datetime.now(UTC)
        await db.commit()
    return _page("confirmed", sub.language)


@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_prompt(
    token: str = Query(..., min_length=10),
    lang: str = Query("es"),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    sub = await _lookup(token, db)
    if sub is None:
        return _page("invalid", lang)
    if sub.unsubscribed_at is not None:
        return _page("unsubscribed", sub.language)
    return _page(
        "unsubscribe_prompt", sub.language, action_url=f"/api/v1/newsletter/unsubscribe?token={token}"
    )


@router.post("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe(
    token: str = Query(..., min_length=10),
    lang: str = Query("es"),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """También sirve de «One-Click» (RFC 8058): el botón de baja de Gmail/Yahoo
    manda este mismo POST sin que nadie vea la página — el cuerpo HTML no les
    importa, solo el 200."""
    sub = await _lookup(token, db)
    if sub is None:
        return _page("invalid", lang)
    if sub.unsubscribed_at is None:
        sub.unsubscribed_at = datetime.now(UTC)
        await db.commit()
    return _page("unsubscribed", sub.language)
