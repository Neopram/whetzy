"""45.2 (ADR-66 E2, E5): al registrarse sale un solo correo, el de verificación,
y la bienvenida sale al verificar, una sola vez.

Antes de este cambio, `register` mandaba en el mismo segundo la verificación y
la bienvenida (prueba del dueño, 2026-10-17, logs de Railway), y el enlace del
correo no llevaba idioma. Con OAuth la cuenta llega verificada: su bienvenida
sale al crearla, y solo entonces.
"""

from __future__ import annotations

import hashlib
import itertools
import re
import secrets
import urllib.parse
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.cookies import OAUTH_STATE_COOKIE
from app.models.email_verification import EmailVerificationToken
from app.models.user import User
from app.services import email as email_svc

AUTH = "/api/v1/auth"
_ip = itertools.count(1)


def _h() -> dict:
    return {"X-Forwarded-For": f"198.51.100.{next(_ip) % 255 or 255}"}


@pytest.fixture
def sent(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str, str]]:
    calls: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        email_svc,
        "_dispatch",
        lambda to, subject, html, unsubscribe_url=None: calls.append((to, subject, html)),
    )
    return calls


def _payload(tag: str, lang: str) -> dict:
    return {
        "email": f"uno-{tag}@example.com",
        "username": f"uno_{tag}",
        "password": "Str0ng!Pass",
        "display_name": "Prueba",
        "language": lang,
        "age_confirmed": True,
    }


def _verify_link(html: str) -> tuple[str, dict[str, str]]:
    url = re.search(r'href="([^"]*/verify-email\?[^"]*)"', html)
    assert url, html
    parsed = urllib.parse.urlsplit(url.group(1).replace("&amp;", "&"))
    return parsed.path, dict(urllib.parse.parse_qsl(parsed.query))


@pytest.mark.parametrize(
    ("lang", "subject"),
    [("es", "Verifica tu email en Whetzy"), ("en", "Verify your Whetzy email")],
)
async def test_register_sends_only_the_verification_email(client, sent, lang, subject) -> None:
    r = await client.post(f"{AUTH}/register", json=_payload(f"r{lang}", lang), headers=_h())
    assert r.status_code == 201, r.text
    assert [s for _, s, _ in sent] == [subject]
    path, query = _verify_link(sent[0][2])
    assert path == "/verify-email"
    assert query["lang"] == lang
    assert query["token"]


async def test_verifying_sends_the_welcome_once(client, sent) -> None:
    r = await client.post(f"{AUTH}/register", json=_payload("v1", "es"), headers=_h())
    assert r.status_code == 201, r.text
    _, query = _verify_link(sent[0][2])
    sent.clear()

    ok = await client.post(f"{AUTH}/verify-email", json={"token": query["token"]}, headers=_h())
    assert ok.status_code == 200, ok.text
    assert [s for _, s, _ in sent] == ["Bienvenido/a a Whetzy, Prueba!"]
    sent.clear()

    again = await client.post(f"{AUTH}/verify-email", json={"token": query["token"]}, headers=_h())
    assert again.status_code == 400
    assert sent == []


async def test_a_live_link_on_a_verified_account_does_not_resend_the_welcome(
    client, db_session, sent
) -> None:
    """Un enlace todavía sin usar sobre una cuenta ya verificada (hoy
    `resend-verification` anula los anteriores, pero nada en `verify_email` lo
    garantiza): se acepta y no repite la bienvenida."""
    payload = _payload("v2", "en")
    assert (await client.post(f"{AUTH}/register", json=payload, headers=_h())).status_code == 201
    token = _verify_link(sent[0][2])[1]["token"]
    sent.clear()
    assert (await client.post(f"{AUTH}/verify-email", json={"token": token}, headers=_h())).status_code == 200
    assert [s for _, s, _ in sent] == ["Welcome to Whetzy, Prueba!"]
    sent.clear()

    user = (await db_session.execute(select(User).where(User.email == payload["email"]))).scalar_one()
    raw = secrets.token_urlsafe(32)
    db_session.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
    )
    await db_session.commit()
    assert (await client.post(f"{AUTH}/verify-email", json={"token": raw}, headers=_h())).status_code == 200
    assert sent == []


async def _oauth(client, code: str) -> None:
    start = await client.get(f"{AUTH}/oauth/test/start", headers=_h(), follow_redirects=False)
    qs = dict(p.split("=", 1) for p in start.headers["location"].split("?")[1].split("&"))
    cookie = next(
        c.split(";", 1)[0]
        for c in start.headers.get_list("set-cookie")
        if c.startswith(f"{OAUTH_STATE_COOKIE}=")
    )
    r = await client.get(
        f"{AUTH}/oauth/test/callback",
        params={"code": code, "state": qs["state"]},
        headers={**_h(), "Cookie": cookie},
        follow_redirects=False,
    )
    assert r.status_code == 302, r.text
    assert "oauth_error" not in r.headers["location"], r.headers["location"]


async def test_oauth_new_account_gets_the_welcome_and_a_returning_one_does_not(client, sent) -> None:
    await _oauth(client, "uno-correo-oauth")
    assert len(sent) == 1
    assert sent[0][1].startswith("Bienvenido/a a Whetzy")
    sent.clear()
    await _oauth(client, "uno-correo-oauth")
    assert sent == []


async def test_oauth_linking_an_existing_verified_account_sends_nothing(client, sent) -> None:
    """La cuenta ya existía (alta con contraseña, verificada): ya recibió su
    bienvenida al verificar y vincular OAuth no la repite."""
    code = "uno-correo-vincular"
    payload = {**_payload("v3", "es"), "email": f"oauth-{code}@example.com"}
    assert (await client.post(f"{AUTH}/register", json=payload, headers=_h())).status_code == 201
    token = _verify_link(sent[0][2])[1]["token"]
    assert (await client.post(f"{AUTH}/verify-email", json={"token": token}, headers=_h())).status_code == 200
    sent.clear()

    await _oauth(client, code)
    assert sent == []
