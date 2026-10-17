"""45.1 (ADR-66 E1): una cuenta creada con OAuth tiene el idioma de la pantalla.

Antes `/start` no sabía nada del idioma y `_find_or_create_user` creaba la
cuenta con el valor por defecto de la columna («es»): quien se registraba con
la app en inglés recibía los correos en español.
"""

from __future__ import annotations

import itertools

from sqlalchemy import select

from app.models.user import User

OAUTH = "/api/v1/auth/oauth"
_ip = itertools.count(40)


def _h() -> dict[str, str]:
    return {"X-Forwarded-For": f"192.0.4.{next(_ip) % 250 + 1}"}


def _cookies(start) -> dict[str, str]:
    # Las cookies van `Secure` y el cliente de test habla http: se reenvían a mano.
    pairs = [
        c.split(";", 1)[0]
        for c in start.headers.get_list("set-cookie")
        if c.startswith("whetzy_oauth_")
    ]
    return {"Cookie": "; ".join(pairs)}


async def _flow(client, code: str, query: str = ""):
    h = _h()
    start = await client.get(f"{OAUTH}/test/start{query}", headers=h, follow_redirects=False)
    assert start.status_code == 302, start.text
    qs = dict(p.split("=", 1) for p in start.headers["location"].split("?")[1].split("&"))
    r = await client.get(
        f"{OAUTH}/test/callback",
        params={"code": code, "state": qs["state"]},
        headers={**h, **_cookies(start)},
        follow_redirects=False,
    )
    assert r.status_code == 302, r.text
    return r


async def _language(db_session, code: str) -> str:
    user = await db_session.scalar(select(User).where(User.email == f"oauth-{code}@example.com"))
    assert user is not None
    await db_session.refresh(user)
    return user.language


async def test_cuenta_nueva_con_lang_en(client, db_session):
    await _flow(client, "lang-en", "?lang=en")
    assert await _language(db_session, "lang-en") == "en"


async def test_cuenta_nueva_sin_lang_queda_por_defecto(client, db_session):
    await _flow(client, "lang-none")
    assert await _language(db_session, "lang-none") == "es"


async def test_lang_no_valido_se_ignora(client, db_session):
    await _flow(client, "lang-fr", "?lang=fr")
    assert await _language(db_session, "lang-fr") == "es"


async def test_cuenta_existente_no_cambia_de_idioma(client, db_session):
    await _flow(client, "lang-keep", "?lang=en")
    # Vuelve a entrar con la pantalla en español: su idioma lo cambia él en Yo.
    await _flow(client, "lang-keep", "?lang=es")
    assert await _language(db_session, "lang-keep") == "en"


async def test_el_callback_borra_la_cookie_del_idioma(client):
    r = await _flow(client, "lang-clear", "?lang=en")
    borradas = [c for c in r.headers.get_list("set-cookie") if c.startswith("whetzy_oauth_lang=")]
    assert borradas and ("Max-Age=0" in borradas[0] or "expires=" in borradas[0].lower())
