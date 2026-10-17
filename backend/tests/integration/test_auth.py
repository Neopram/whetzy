"""Integration tests for auth endpoints.

Covers: register, login, me, refresh, delete account.
All tests use the conftest fixtures (client, user, auth_headers).

Each test sends a unique X-Forwarded-For header so the in-memory rate limiter
(auth_limit=12/min) gives every test its own bucket and no test is blocked by
its neighbours' requests.
"""

from __future__ import annotations

import itertools

AUTH = "/api/v1/auth"

# Each test gets its own /8 subnet to avoid sharing rate-limit buckets.
_ip_counter = itertools.count(1)


def _unique_ip() -> str:
    """Return a unique RFC-5737 documentation IP so each test has its own bucket."""
    n = next(_ip_counter)
    return f"192.0.2.{n % 255 or 255}"


def _h(extra: dict | None = None) -> dict:
    """Build a headers dict with a unique IP and any extra headers."""
    headers = {"X-Forwarded-For": _unique_ip()}
    if extra:
        headers.update(extra)
    return headers


# ── register ──────────────────────────────────────────────────────────────────


async def test_register_happy_path(client):
    payload = {
        "email": "new@example.com",
        "username": "newuser01",
        "password": "Str0ng!Pass",
        "display_name": "New User",
        "language": "en",
        "age_confirmed": True,
    }
    r = await client.post(f"{AUTH}/register", json=payload, headers=_h())
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["access_token"]


async def test_register_duplicate_email_returns_409(client):
    h = _h()
    payload = {
        "email": "dup@example.com",
        "username": "dupuser1",
        "password": "Str0ng!Pass",
        "display_name": "Dup",
        "language": "es",
        "age_confirmed": True,
    }
    r1 = await client.post(f"{AUTH}/register", json=payload, headers=h)
    assert r1.status_code == 201

    payload2 = dict(payload)
    payload2["username"] = "dupuser2"  # different username, same email
    r2 = await client.post(f"{AUTH}/register", json=payload2, headers=h)
    assert r2.status_code == 409


async def test_register_duplicate_username_returns_409(client):
    h = _h()
    payload = {
        "email": "first@example.com",
        "username": "sharedname",
        "password": "Str0ng!Pass",
        "display_name": "First",
        "language": "es",
        "age_confirmed": True,
    }
    await client.post(f"{AUTH}/register", json=payload, headers=h)

    payload2 = dict(payload)
    payload2["email"] = "second@example.com"  # different email, same username
    r = await client.post(f"{AUTH}/register", json=payload2, headers=h)
    assert r.status_code == 409


async def test_register_without_age_confirmed_returns_400(client):
    payload = {
        "email": "underage@example.com",
        "username": "underage01",
        "password": "Str0ng!Pass",
        "display_name": "No Age",
        "language": "es",
        "age_confirmed": False,
    }
    r = await client.post(f"{AUTH}/register", json=payload, headers=_h())
    assert r.status_code == 400
    assert "age" in r.json()["detail"].lower()


async def test_register_missing_required_field_returns_422(client):
    # Missing password
    r = await client.post(
        f"{AUTH}/register",
        json={"email": "x@example.com", "username": "xuser"},
        headers=_h(),
    )
    assert r.status_code == 422


async def test_register_rejects_blocked_word_in_display_name(client):
    """19.11: filtro de palabras al crear la cuenta (App Store 1.2)."""
    payload = {
        "email": "rude@example.com",
        "username": "rudeuser01",
        "password": "Str0ng!Pass",
        "display_name": "Soy una mierda",
        "language": "es",
        "age_confirmed": True,
    }
    r = await client.post(f"{AUTH}/register", json=payload, headers=_h())
    assert r.status_code == 422


# ── login ─────────────────────────────────────────────────────────────────────


async def test_login_happy_path(client, user):
    r = await client.post(
        f"{AUTH}/login",
        data={"username": user.email, "password": "Passw0rd!"},
        headers=_h({"Content-Type": "application/x-www-form-urlencoded"}),
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password_returns_401(client, user):
    r = await client.post(
        f"{AUTH}/login",
        data={"username": user.email, "password": "WrongPassword!"},
        headers=_h({"Content-Type": "application/x-www-form-urlencoded"}),
    )
    assert r.status_code == 401


async def test_login_unknown_email_returns_401(client):
    r = await client.post(
        f"{AUTH}/login",
        data={"username": "nobody@example.com", "password": "Whatever!1"},
        headers=_h({"Content-Type": "application/x-www-form-urlencoded"}),
    )
    assert r.status_code == 401


# ── me ────────────────────────────────────────────────────────────────────────


async def test_me_happy_path(client):
    # Register a user with a fully valid email so FastAPI's UserRead (EmailStr)
    # serializes without error. The conftest `user` fixture uses @whetzy.test
    # which email-validator rejects as a reserved TLD.
    h = _h()
    reg = await client.post(f"{AUTH}/register", json={
        "email": "metest@example.com",
        "username": "metest01",
        "password": "Str0ng!Pass",
        "display_name": "Me Tester",
        "language": "en",
        "age_confirmed": True,
    }, headers=h)
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    r = await client.get(f"{AUTH}/me", headers=_h({"Authorization": f"Bearer {token}"}))
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "metest@example.com"
    assert data["username"] == "metest01"


async def test_me_no_token_returns_401(client):
    r = await client.get(f"{AUTH}/me", headers=_h())
    assert r.status_code == 401


async def test_me_invalid_token_returns_401(client):
    r = await client.get(
        f"{AUTH}/me",
        headers=_h({"Authorization": "Bearer notavalidtoken"}),
    )
    assert r.status_code == 401


# ── refresh ───────────────────────────────────────────────────────────────────


async def test_refresh_happy_path(client, user):
    h = _h({"Content-Type": "application/x-www-form-urlencoded"})
    login_r = await client.post(
        f"{AUTH}/login",
        data={"username": user.email, "password": "Passw0rd!"},
        headers=h,
    )
    refresh_token = login_r.json()["refresh_token"]

    r = await client.post(
        f"{AUTH}/refresh",
        json={"refresh_token": refresh_token},
        headers=_h(),
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_refresh_invalid_token_returns_401(client):
    r = await client.post(
        f"{AUTH}/refresh",
        json={"refresh_token": "bogus.token.value"},
        headers=_h(),
    )
    assert r.status_code == 401


async def test_refresh_rejected_after_jwt_version_bump(client, user, db_session):
    """S.1: un refresh token emitido antes de subir jwt_version (cambio de
    contraseña, "cerrar sesión en todos los dispositivos", activar 2FA) debe
    quedar inválido, igual que ya pasa con el access token en /auth/me."""
    h = _h({"Content-Type": "application/x-www-form-urlencoded"})
    login_r = await client.post(
        f"{AUTH}/login",
        data={"username": user.email, "password": "Passw0rd!"},
        headers=h,
    )
    refresh_token = login_r.json()["refresh_token"]

    user.jwt_version += 1
    await db_session.commit()

    r = await client.post(
        f"{AUTH}/refresh",
        json={"refresh_token": refresh_token},
        headers=_h(),
    )
    assert r.status_code == 401


async def test_refresh_rejected_after_logout(client, user, db_session):
    """41.18: logout solo borraba cookies y registraba el evento — un refresh
    capturado antes de cerrar sesión seguía dando tokens nuevos hasta sus 30
    días. Ahora logout sube `jwt_version`, el mismo mecanismo que ya usan el
    cambio de contraseña y su reset."""
    h = _h({"Content-Type": "application/x-www-form-urlencoded"})
    login_r = await client.post(
        f"{AUTH}/login",
        data={"username": user.email, "password": "Passw0rd!"},
        headers=h,
    )
    tokens = login_r.json()
    refresh_token = tokens["refresh_token"]

    logout_r = await client.post(
        f"{AUTH}/logout",
        headers=_h({"Authorization": f"Bearer {tokens['access_token']}"}),
    )
    assert logout_r.status_code == 200

    r = await client.post(
        f"{AUTH}/refresh",
        json={"refresh_token": refresh_token},
        headers=_h(),
    )
    assert r.status_code == 401


# ── delete account ────────────────────────────────────────────────────────────


async def test_delete_account_happy_path(client, auth_headers):
    r = await client.delete(
        f"{AUTH}/me/account",
        headers=_h(auth_headers),
    )
    assert r.status_code == 200
    data = r.json()
    assert "message" in data


async def test_delete_account_clears_session_cookies(client, auth_headers):
    """2026-10-17, iPhone del dueño: tras borrar la cuenta, «atrás» volvía a Hoy
    con la sesión aún en el navegador. El servidor ya la rechaza (403), pero la
    respuesta del borrado también tiene que tirar las cookies de sesión."""
    r = await client.delete(f"{AUTH}/me/account", headers=_h(auth_headers))
    assert r.status_code == 200
    borradas = [
        h for h in r.headers.get_list("set-cookie")
        if ("Max-Age=0" in h or "expires=Thu, 01 Jan 1970" in h)
    ]
    nombres = {h.split("=", 1)[0] for h in borradas}
    from app.core.cookies import ACCESS_COOKIE, REFRESH_COOKIE

    assert {ACCESS_COOKIE, REFRESH_COOKIE} <= nombres, r.headers.get_list("set-cookie")


async def test_delete_account_no_token_returns_401(client):
    r = await client.delete(f"{AUTH}/me/account", headers=_h())
    assert r.status_code == 401
