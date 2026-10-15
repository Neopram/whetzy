"""El panel de administración es solo del dueño (decisión del 2026-10-15).

`require_admin` aceptaba también el rol `admin`; ahora solo `owner`. Se prueba
contra una ruta real del panel con los tres roles.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


async def _token(db: AsyncSession, role: str) -> str:
    u = User(
        id=uuid.uuid4(),
        email=f"{role}-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"{role}{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name=role,
        language="es",
        role=role,
        is_admin=role != "user",
    )
    db.add(u)
    await db.commit()
    return create_access_token(u.id)


@pytest.mark.asyncio
@pytest.mark.parametrize(("role", "expected"), [("owner", 200), ("admin", 403), ("user", 403)])
async def test_solo_el_dueno_entra_al_panel(
    client: AsyncClient, db_session: AsyncSession, role: str, expected: int
) -> None:
    token = await _token(db_session, role)
    r = await client.get("/api/v1/admin/ops/deploy-info", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == expected, r.text
