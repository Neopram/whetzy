"""Preferencias de correo: baja de los correos de marketing.

La política publicada promete que todos los correos se pueden cancelar
(`legal.privacyCanSpam`). Hasta el 2026-10-01 el único mecanismo era una cabecera
``mailto:`` a una dirección que nadie procesaba.

- ``GET  /email/unsubscribe?token=…`` — el enlace del correo: da de baja y lo dice.
- ``POST /email/unsubscribe?token=…`` — «One-Click» (RFC 8058): el botón «Darse de
  baja» de Gmail o Yahoo hace este POST sin abrir nada.
- ``PATCH /email/preferences`` — el interruptor de Yo → Ajustes.

Solo cubre el marketing (hoy, el correo de reactivación con código). Los correos de
servicio (verificación, contraseña, recibos, aviso de renovación) no se pueden
desactivar: son parte del contrato.
"""

from __future__ import annotations

import html
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user, verify_token
from app.models.user import User

router = APIRouter()

_PAGE = """<!doctype html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Whetzy</title>
<style>body{{font-family:system-ui,sans-serif;background:#0D1015;color:#E8ECF1;
display:grid;place-items:center;min-height:100vh;margin:0;padding:16px}}
main{{max-width:28rem}}a{{color:#FF8A5B}}</style></head>
<body><main><h1>{title}</h1><p>{body}</p><p><a href="{home}">{back}</a></p></main></body></html>"""

_TEXT = {
    "es": {
        "title": "Te has dado de baja",
        "body": "No recibirás más correos de ofertas de Whetzy. Los correos de tu cuenta "
        "(verificación, contraseña, recibos) siguen llegando. Puedes volver a activarlos en "
        "Yo → Ajustes.",
        "back": "Volver a Whetzy",
    },
    "en": {
        "title": "You're unsubscribed",
        "body": "You won't get any more offer emails from Whetzy. Account emails "
        "(verification, password, receipts) still arrive. You can turn offers back on in "
        "You → Settings.",
        "back": "Back to Whetzy",
    },
}


async def _opt_out(token: str, db: AsyncSession) -> User:
    try:
        payload = verify_token(token, expected_type="unsubscribe")
        user_id = uuid.UUID(str(payload.sub))
    except (HTTPException, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_token") from exc
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_token")
    user.marketing_emails_opt_out = True
    await db.commit()
    return user


@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_page(
    token: str = Query(..., min_length=10), db: AsyncSession = Depends(get_db)
) -> HTMLResponse:
    from app.core.config import settings

    user = await _opt_out(token, db)
    lang = user.language if user.language in _TEXT else "es"
    t = _TEXT[lang]
    return HTMLResponse(
        _PAGE.format(
            lang=lang,
            title=html.escape(t["title"]),
            body=html.escape(t["body"]),
            back=html.escape(t["back"]),
            home=html.escape(settings.FRONTEND_BASE_URL),
        )
    )


@router.post("/unsubscribe", status_code=status.HTTP_200_OK)
async def unsubscribe_one_click(
    token: str = Query(..., min_length=10), db: AsyncSession = Depends(get_db)
) -> dict[str, bool]:
    await _opt_out(token, db)
    return {"unsubscribed": True}


class EmailPreferences(BaseModel):
    marketing: bool


@router.patch("/preferences")
async def update_email_preferences(
    body: EmailPreferences,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    user.marketing_emails_opt_out = not body.marketing
    await db.commit()
    return {"marketing": not user.marketing_emails_opt_out}
