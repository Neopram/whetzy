"""Verificación en dos pasos de punta a punta.

Hasta el 2026-10-02 la 2FA se podía activar (`/auth/2fa/setup` + `enable`) y el
login la ignoraba: con la contraseña sola había sesión. Además, rehacer el alta
la apagaba sin código y no había forma de desactivarla con uno. Estos tests fijan
el comportamiento correcto.
"""

from __future__ import annotations

import uuid

import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User

PASSWORD = "Passw0rd!long"


async def _user(db: AsyncSession) -> User:
    uid = uuid.uuid4()
    u = User(id=uid, email=f"tf{uid.hex[:8]}@example.com", username=f"tf{uid.hex[:8]}",
             hashed_password=get_password_hash(PASSWORD), display_name="TF", language="es")
    db.add(u)
    await db.commit()
    return u


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


async def _login(client: AsyncClient, user: User):
    client.cookies.clear()
    return await client.post("/api/v1/auth/login", data={"username": user.email, "password": PASSWORD})


async def _enable(client: AsyncClient, user: User) -> tuple[pyotp.TOTP, list[str]]:
    setup = await client.post("/api/v1/auth/2fa/setup", headers=_auth(user))
    assert setup.status_code == 200, setup.text
    body = setup.json()
    assert "<svg" in body["qr_svg"] and body["secret"] in body["qr_uri"]
    totp = pyotp.TOTP(body["secret"])
    r = await client.post("/api/v1/auth/2fa/enable", json={"totp_code": totp.now()}, headers=_auth(user))
    assert r.status_code == 200, r.text
    return totp, body["backup_codes"]


@pytest.mark.asyncio
async def test_without_2fa_login_is_unchanged(client: AsyncClient, db_session: AsyncSession):
    user = await _user(db_session)
    r = await _login(client, user)
    assert r.status_code == 200 and "access_token" in r.json()


@pytest.mark.asyncio
async def test_with_2fa_the_password_alone_opens_no_session(client: AsyncClient, db_session: AsyncSession):
    user = await _user(db_session)
    totp, _ = await _enable(client, user)

    r = await _login(client, user)
    body = r.json()
    assert r.status_code == 200 and body["mfa_required"] is True
    assert "access_token" not in body
    assert "whetzy_access" not in r.cookies
    # El token del primer paso no sirve de sesión.
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['mfa_token']}"})
    assert me.status_code == 401

    bad = await client.post("/api/v1/auth/2fa/login", json={"code": "000000", "mfa_token": body["mfa_token"]})
    assert bad.status_code == 400
    ok = await client.post("/api/v1/auth/2fa/login", json={"code": totp.now(), "mfa_token": body["mfa_token"]})
    assert ok.status_code == 200 and "access_token" in ok.json()
    assert "whetzy_access" in ok.cookies


@pytest.mark.asyncio
async def test_a_backup_code_works_once(client: AsyncClient, db_session: AsyncSession):
    user = await _user(db_session)
    _, backup = await _enable(client, user)

    for expected in (200, 400):
        token = (await _login(client, user)).json()["mfa_token"]
        r = await client.post("/api/v1/auth/2fa/login", json={"code": backup[0], "mfa_token": token})
        assert r.status_code == expected
    status = (await client.get("/api/v1/auth/2fa/status", headers=_auth(user))).json()
    assert status == {"enabled": True, "backup_codes_left": 9}


@pytest.mark.asyncio
async def test_wrong_codes_trigger_the_lockout(client: AsyncClient, db_session: AsyncSession):
    user = await _user(db_session)
    await _enable(client, user)
    token = (await _login(client, user)).json()["mfa_token"]
    codes = []
    for _ in range(6):
        r = await client.post("/api/v1/auth/2fa/login", json={"code": "123456", "mfa_token": token})
        codes.append(r.status_code)
    assert codes[:5] == [400] * 5 and codes[5] == 429


@pytest.mark.asyncio
async def test_setup_cannot_silently_turn_2fa_off(client: AsyncClient, db_session: AsyncSession):
    """Con una sesión robada, rehacer el alta apagaba la 2FA sin código."""
    user = await _user(db_session)
    await _enable(client, user)
    r = await client.post("/api/v1/auth/2fa/setup", headers=_auth(user))
    assert r.status_code == 409
    assert (await client.get("/api/v1/auth/2fa/status", headers=_auth(user))).json()["enabled"] is True


@pytest.mark.asyncio
async def test_disabling_needs_a_code(client: AsyncClient, db_session: AsyncSession):
    user = await _user(db_session)
    totp, _ = await _enable(client, user)
    bad = await client.post("/api/v1/auth/2fa/disable", json={"code": "000000"}, headers=_auth(user))
    assert bad.status_code == 400
    ok = await client.post("/api/v1/auth/2fa/disable", json={"code": totp.now()}, headers=_auth(user))
    assert ok.status_code == 200
    assert "access_token" in (await _login(client, user)).json()


@pytest.mark.asyncio
async def test_oauth_with_2fa_asks_for_the_code_without_a_token_in_the_url(
    client: AsyncClient, db_session: AsyncSession
):
    start = await client.get("/api/v1/auth/oauth/test/start", follow_redirects=False)
    if start.status_code == 404:
        pytest.skip("proveedor OAuth de pruebas no disponible en este entorno")
    state = start.headers["location"].split("state=")[1].split("&")[0]
    first = await client.get(
        f"/api/v1/auth/oauth/test/callback?code=tfa&state={state}", follow_redirects=False
    )
    assert first.status_code == 302 and "whetzy_access" in first.cookies

    user = (
        await db_session.execute(select(User).where(User.email == "oauth-tfa@example.com"))
    ).scalar_one()
    totp, _ = await _enable(client, user)

    client.cookies.clear()
    start = await client.get("/api/v1/auth/oauth/test/start", follow_redirects=False)
    state = start.headers["location"].split("state=")[1].split("&")[0]
    second = await client.get(
        f"/api/v1/auth/oauth/test/callback?code=tfa&state={state}", follow_redirects=False
    )
    assert second.status_code == 302
    assert second.headers["location"].endswith("/auth?mfa=1")
    assert "whetzy_access" not in second.cookies and "whetzy_mfa" in second.cookies

    # La cookie es Secure y el cliente de test habla http: se manda a mano, como
    # haría el navegador sobre https. El cuerpo no lleva token: se lee de la cookie.
    mfa = second.cookies["whetzy_mfa"]
    client.cookies.clear()
    ok = await client.post(
        "/api/v1/auth/2fa/login", json={"code": totp.now()}, headers={"Cookie": f"whetzy_mfa={mfa}"}
    )
    assert ok.status_code == 200 and "access_token" in ok.json()
