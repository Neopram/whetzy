"""La cuenta de dueno sale de OWNER_EMAIL/OWNER_PASSWORD, no del repo.

Antes la creaba una migracion con un hash versionado y el rol `superuser`,
que `/admin` rechaza con 403. Estos tests fijan lo que la sustituye.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.services.bootstrap_owner import OwnerConfigError, ensure_owner

PW = "una-contrasena-larga-1"


async def _get(db: AsyncSession, email: str) -> User:
    return (await db.execute(select(User).where(User.email == email))).scalar_one()


@pytest.mark.asyncio
async def test_sin_variables_no_hace_nada(db_session: AsyncSession) -> None:
    assert await ensure_owner(db_session, "", "") == "skipped"
    assert (await db_session.execute(select(User))).first() is None


@pytest.mark.asyncio
@pytest.mark.parametrize("email,pw", [("dueno@whetzy.com", ""), ("", PW), ("dueno@whetzy.com", "corta")])
async def test_configuracion_a_medias_falla(db_session: AsyncSession, email: str, pw: str) -> None:
    with pytest.raises(OwnerConfigError):
        await ensure_owner(db_session, email, pw)


@pytest.mark.asyncio
async def test_crea_owner_verificado(db_session: AsyncSession) -> None:
    assert await ensure_owner(db_session, " Dueno@Whetzy.com ", PW) == "created"
    u = await _get(db_session, "dueno@whetzy.com")
    assert (u.role, u.is_admin, u.email_verified, u.is_active) == ("owner", True, True, True)
    assert u.hashed_password and verify_password(PW, u.hashed_password)
    assert await ensure_owner(db_session, "dueno@whetzy.com", PW) == "unchanged"


@pytest.mark.asyncio
async def test_repara_la_cuenta_de_la_migracion_antigua(db_session: AsyncSession) -> None:
    db_session.add(
        User(
            email="admin@whetzy.com",
            username="admin",
            display_name="Admin",
            hashed_password=None,  # lo que deja 20260924_owner_role si conservaba el hash filtrado
            role="superuser",
            is_admin=True,
        )
    )
    await db_session.commit()
    assert await ensure_owner(db_session, "admin@whetzy.com", PW) == "updated"
    u = await _get(db_session, "admin@whetzy.com")
    assert u.role == "owner" and u.email_verified
    assert u.hashed_password and verify_password(PW, u.hashed_password)


@pytest.mark.asyncio
async def test_cambiar_la_variable_cambia_la_contrasena(db_session: AsyncSession) -> None:
    await ensure_owner(db_session, "dueno@whetzy.com", PW)
    assert await ensure_owner(db_session, "dueno@whetzy.com", PW + "x") == "updated"
    u = await _get(db_session, "dueno@whetzy.com")
    assert u.hashed_password and not verify_password(PW, u.hashed_password)


@pytest.mark.asyncio
async def test_username_ocupado_no_rompe(db_session: AsyncSession) -> None:
    db_session.add(
        User(email="otro@x.com", username="dueno", display_name="x", hashed_password=get_password_hash(PW))
    )
    await db_session.commit()
    assert await ensure_owner(db_session, "dueno@whetzy.com", PW) == "created"
    assert (await _get(db_session, "dueno@whetzy.com")).username == "dueno_2"


@pytest.mark.asyncio
async def test_el_owner_entra_y_ve_el_admin(client: AsyncClient, db_session: AsyncSession) -> None:
    await ensure_owner(db_session, "dueno@whetzy.com", PW)
    r = await client.post("/api/v1/auth/login", data={"username": "dueno@whetzy.com", "password": PW})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    r = await client.get("/api/v1/admin/ops/health", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code != 403, r.text
