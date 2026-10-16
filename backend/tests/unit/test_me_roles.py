"""`/auth/me` dice qué puede ver la cuenta en Perfil (auditoría de pantallas, 2026-10-16).

- «Instructor» es solo para creadores (decisión del dueño): plan Creador, o
  dueño/admin, que montan el catálogo propio. La misma regla que
  `create_course` aplica con `CREATOR_PLAN_REQUIRED`.
- «Admin» es solo del dueño desde #202.

Antes `/auth/me` no devolvía `is_admin` ni el plan, así que el enlace «Admin»
de Perfil no se veía nunca, ni para el dueño, e «Instructor» se veía para todos.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


async def _token(db: AsyncSession, *, role: str = "user", tier: str | None = None) -> str:
    u = User(
        id=uuid.uuid4(),
        email=f"{role}-{uuid.uuid4().hex[:8]}@example.com",
        username=f"{role}{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name=role,
        language="es",
        role=role,
        is_admin=role != "user",
        is_premium=tier is not None,
        subscription_tier=tier,
    )
    db.add(u)
    await db.commit()
    return create_access_token(u.id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("role", "tier", "creator", "owner"),
    [
        ("user", None, False, False),
        ("user", "pro", False, False),
        ("user", "creator", True, False),
        ("admin", None, True, False),
        ("owner", None, True, True),
    ],
)
async def test_me_dice_si_ve_instructor_y_admin(
    client: AsyncClient, db_session: AsyncSession, role: str, tier: str | None, creator: bool, owner: bool
) -> None:
    token = await _token(db_session, role=role, tier=tier)
    r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["can_create_courses"] is creator
    assert body["is_owner"] is owner
