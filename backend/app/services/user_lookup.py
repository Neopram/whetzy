"""Búsqueda de cuentas por email sin distinguir caja (43.2, ADR-65 D10).

Las cuentas creadas antes de normalizar guardan el email con su caja original.
La comparten el registro, el login, el reenvío de verificación, el olvido de
contraseña y OAuth: antes OAuth comparaba con `==` y creaba una cuenta nueva
para `legacy@example.com` existiendo `Legacy@Example.com`.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def user_by_email(db: AsyncSession, email: str) -> User | None:
    """Si dos cuentas viejas solo difieren en la caja, gana la más antigua, en
    vez de reventar con `MultipleResultsFound`."""
    result = await db.execute(
        select(User)
        .where(func.lower(User.email) == normalize_email(email))
        .order_by(User.created_at)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def username_taken(db: AsyncSession, username: str) -> bool:
    """`MARIA_X` y `maria_x` son el mismo usuario a ojos de una persona."""
    result = await db.execute(
        select(User.id).where(func.lower(User.username) == username.strip().lower()).limit(1)
    )
    return result.scalar_one_or_none() is not None
