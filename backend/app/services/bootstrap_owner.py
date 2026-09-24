"""Crea o actualiza la cuenta de dueno desde `OWNER_EMAIL` / `OWNER_PASSWORD`.

Sustituye al usuario que insertaba la migracion `20260922_setup_admin` con un
hash de contrasena versionado en el repo y un rol (`superuser`) que `/admin`
no acepta. Aqui la contrasena solo existe en las variables del entorno.

Idempotente: se corre en cada arranque desde `scripts/start.sh`. Con las dos
variables vacias no hace nada; con una sola, falla (una configuracion a
medias es un error, no un «no pasa nada»).
"""

from __future__ import annotations

import asyncio
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.core.security import get_password_hash, verify_password
from app.models.user import User

MIN_PASSWORD_LENGTH = 12


class OwnerConfigError(ValueError):
    pass


async def _free_username(db: AsyncSession, email: str) -> str:
    base = re.sub(r"[^a-z0-9_]", "_", email.split("@")[0].lower())[:40] or "owner"
    candidate, n = base, 1
    while (await db.execute(select(User.id).where(User.username == candidate))).first():
        n += 1
        candidate = f"{base}_{n}"
    return candidate


async def ensure_owner(db: AsyncSession, email: str, password: str) -> str:
    """Devuelve "skipped", "created" o "updated". No escribe si no hace falta."""
    email = email.strip().lower()
    if not email and not password:
        return "skipped"
    if not email or not password:
        raise OwnerConfigError("OWNER_EMAIL y OWNER_PASSWORD van juntos: falta uno de los dos")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise OwnerConfigError(f"OWNER_PASSWORD necesita al menos {MIN_PASSWORD_LENGTH} caracteres")

    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None:
        db.add(
            User(
                email=email,
                username=await _free_username(db, email),
                display_name="Owner",
                hashed_password=get_password_hash(password),
                role="owner",
                is_admin=True,
                is_active=True,
                email_verified=True,
            )
        )
        await db.commit()
        return "created"

    changed = False
    if user.role != "owner" or not user.is_admin:
        user.role, user.is_admin = "owner", True
        changed = True
    if not user.is_active or not user.email_verified:
        user.is_active, user.email_verified = True, True
        changed = True
    if not user.hashed_password or not verify_password(password, user.hashed_password):
        user.hashed_password = get_password_hash(password)
        changed = True
    if changed:
        await db.commit()
        return "updated"
    return "unchanged"


async def main() -> None:
    async with AsyncSessionLocal() as db:
        result = await ensure_owner(db, settings.OWNER_EMAIL, settings.OWNER_PASSWORD)
    # Nunca imprimir la contrasena; el email si, para saber a quien afecto.
    print(f"[owner] {result}" + (f": {settings.OWNER_EMAIL.strip().lower()}" if result != "skipped" else ""))


if __name__ == "__main__":
    asyncio.run(main())
