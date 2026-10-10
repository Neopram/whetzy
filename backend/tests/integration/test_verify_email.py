"""`POST /auth/verify-email` y `/auth/resend-verification` (0.2).

El endpoint reutilizaba `ResetPasswordRequest` -- que exige `new_password`
-- así que cualquier cliente que mandara solo `{token}` (lo correcto aquí)
recibía un 422 antes de llegar a la lógica: nadie lo notó porque no había
ni página en el frontend ni test que lo llamara de verdad.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.email_verification import EmailVerificationToken
from app.models.user import User

AUTH = "/api/v1/auth"


async def _unverified_user(db: AsyncSession) -> User:
    tag = uuid.uuid4().hex[:8]
    user = User(
        id=uuid.uuid4(),
        email=f"verify-{tag}@whetzy.test",
        username=f"verify{tag}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Verify Me",
        language="es",
        email_verified=False,
    )
    db.add(user)
    await db.commit()
    return user


async def _token_for(db: AsyncSession, user: User, *, expired: bool = False, used: bool = False) -> str:
    raw = secrets.token_urlsafe(32)
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            expires_at=datetime.now(UTC) + (timedelta(hours=-1) if expired else timedelta(hours=24)),
            used=used,
        )
    )
    await db.commit()
    return raw


@pytest.mark.asyncio
async def test_verify_email_accepts_only_a_token_no_password(client, db_session) -> None:
    """El cuerpo correcto es solo {token}: un new_password no debería hacer
    falta ni para una contraseña válida ni para ninguna otra."""
    user = await _unverified_user(db_session)
    token = await _token_for(db_session, user)

    res = await client.post(f"{AUTH}/verify-email", json={"token": token})

    assert res.status_code == 200, res.text


@pytest.mark.asyncio
async def test_verify_email_marks_the_user_verified(client, db_session) -> None:
    user = await _unverified_user(db_session)
    token = await _token_for(db_session, user)

    res = await client.post(f"{AUTH}/verify-email", json={"token": token})
    assert res.status_code == 200, res.text

    await db_session.refresh(user)
    assert user.email_verified is True


@pytest.mark.asyncio
async def test_verify_email_rejects_an_expired_token(client, db_session) -> None:
    user = await _unverified_user(db_session)
    token = await _token_for(db_session, user, expired=True)

    res = await client.post(f"{AUTH}/verify-email", json={"token": token})

    assert res.status_code == 400
    await db_session.refresh(user)
    assert user.email_verified is False


@pytest.mark.asyncio
async def test_verify_email_rejects_an_already_used_token(client, db_session) -> None:
    user = await _unverified_user(db_session)
    token = await _token_for(db_session, user, used=True)

    res = await client.post(f"{AUTH}/verify-email", json={"token": token})

    assert res.status_code == 400


@pytest.mark.asyncio
async def test_verify_email_rejects_an_unknown_token(client) -> None:
    res = await client.post(f"{AUTH}/verify-email", json={"token": "no-such-token"})
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_resend_verification_always_returns_200(client) -> None:
    """No revela si el email existe o ya está verificado (red line 5)."""
    res = await client.post(f"{AUTH}/resend-verification", json={"email": "nobody@whetzy.test"})
    assert res.status_code == 200
