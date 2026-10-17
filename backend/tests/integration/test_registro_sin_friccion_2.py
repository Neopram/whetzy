"""43.2 (ADR-65 D10), hallazgos del verificador §7 del 2026-10-17.

- OAuth buscaba la cuenta por `User.email == email` sin normalizar: una cuenta
  vieja `Legacy@Example.com` no se encontraba al entrar con Google/GitHub con
  `legacy@example.com` y se creaba otra.
- El usuario único distinguía mayúsculas: `MARIA_X` se registraba con
  `maria_x` ya en uso.
"""

from __future__ import annotations

import itertools

from sqlalchemy import func, select

from app.api.v1.endpoints.oauth import _find_or_create_user
from app.core.security import get_password_hash
from app.models.user import User

AUTH = "/api/v1/auth"
_ip = itertools.count(1)


def _h() -> dict:
    return {"X-Forwarded-For": f"203.0.113.{next(_ip) % 255 or 255}"}


async def test_oauth_encuentra_la_cuenta_vieja_con_mayusculas(db_session):
    db_session.add(
        User(
            email="Legacy@Example.com",
            username="legacy_oauth",
            hashed_password=get_password_hash("Str0ng!Pass"),
            display_name="Legacy",
            language="es",
            age_confirmed=True,
            email_verified=True,
        )
    )
    await db_session.commit()

    user = await _find_or_create_user(db_session, "legacy@EXAMPLE.com", "test", "prov-1")

    assert user.username == "legacy_oauth"
    total = await db_session.scalar(
        select(func.count()).select_from(User).where(func.lower(User.email) == "legacy@example.com")
    )
    assert total == 1


async def test_oauth_guarda_el_email_nuevo_en_minusculas(db_session):
    user = await _find_or_create_user(db_session, " Nueva@Example.COM ", "test", "prov-2")
    assert user.email == "nueva@example.com"


async def test_el_usuario_no_se_repite_cambiando_mayusculas(client):
    first = {
        "email": "uno@example.com", "username": "maria_x", "password": "Str0ng!Pass",
        "display_name": "Uno", "language": "es", "age_confirmed": True,
    }
    assert (await client.post(f"{AUTH}/register", json=first, headers=_h())).status_code == 201
    second = {**first, "email": "dos@example.com", "username": "MARIA_X"}
    r = await client.post(f"{AUTH}/register", json=second, headers=_h())
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "username_taken"
