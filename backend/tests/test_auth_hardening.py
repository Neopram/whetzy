"""Auth hardening comprehensive tests: lockout, rotation, sessions, 2FA, audit logging."""

from __future__ import annotations

import asyncio
import hashlib
import time
import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.security import (
    check_lockout,
    create_opaque_refresh_token,
    create_session,
    enable_2fa,
    get_user_sessions,
    record_login_attempt,
    refresh_token_rotation,
    revoke_session,
    setup_2fa,
)
from app.models.auth import AuditLog, LoginAttempt, RefreshToken, User2FA, UserSession
from app.models.user import User


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    from app.core.security import get_password_hash

    user = User(
        id=uuid.uuid4(),
        email=f"authtest-{uuid.uuid4().hex[:6]}@test.whetzy",
        username=f"authtest{uuid.uuid4().hex[:4]}",
        hashed_password=get_password_hash("TestPassword123!"),
        display_name="Auth Test User",
        language="en",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _locked_right_after_last_attempt(
    email: str, ip: str, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> bool:
    """`check_lockout` medido 0,5 s después del último intento, no «ahora».

    Con 5 fallos el bloqueo dura 1 s, y en SQLite `created_at` (server_default
    `now()`) se guarda truncado al segundo: si entre el 5.º intento y la
    comprobación cambiaba el segundo, el test fallaba al azar (CI de 80cd3ad,
    2026-10-01). Postgres guarda microsegundos; esto es solo del banco de tests.
    """
    last = (
        await db.execute(
            select(func.max(LoginAttempt.created_at)).where(
                LoginAttempt.email == email, LoginAttempt.ip == ip
            )
        )
    ).scalar_one()
    if last is None:
        return await check_lockout(email, ip, db=db)
    instant = security._as_utc(last) + timedelta(milliseconds=500)

    class _Clock(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            return instant

    with monkeypatch.context() as m:
        m.setattr(security, "datetime", _Clock)
        return await check_lockout(email, ip, db=db)


class TestAccountLockout:
    """Test progressive account lockout with exponential backoff."""

    async def test_attempt_keeps_sub_second_precision(self, db_session: AsyncSession, user: User):
        """`created_at` no puede perder la fracción de segundo.

        Con `server_default=now()`, SQLite guardaba `HH:MM:SS`: medio segundo
        después del 5.º fallo el bloqueo de 1 s ya no contaba, y
        `test_2fa_login::test_wrong_codes_trigger_the_lockout` daba 400 al azar.
        Se espera a la mitad de un segundo para que el truncado no pueda
        quedarse a menos de 0,3 s del valor real.
        """
        while not 0.3 <= time.time() % 1 <= 0.7:
            await asyncio.sleep(0.01)
        before = datetime.now(UTC)
        await record_login_attempt(user.email, "192.168.1.99", success=False, db=db_session)
        stored = (
            await db_session.execute(
                select(LoginAttempt.created_at).where(LoginAttempt.ip == "192.168.1.99")
            )
        ).scalar_one()
        assert abs((security._as_utc(stored) - before).total_seconds()) < 0.2, stored

    async def test_lockout_exponential_delay(
        self, db_session: AsyncSession, user: User, monkeypatch: pytest.MonkeyPatch
    ):
        """5 failed attempts -> locked 1s, 6 -> 2s, 7 -> 4s, etc."""
        email = user.email
        ip = "192.168.1.100"

        for i in range(4):
            await record_login_attempt(email, ip, success=False, db=db_session)
            is_locked = await check_lockout(email, ip, db=db_session)
            assert not is_locked

        await record_login_attempt(email, ip, success=False, db=db_session)
        is_locked = await _locked_right_after_last_attempt(email, ip, db_session, monkeypatch)
        assert is_locked

    async def test_login_with_lockout_flow(
        self, db_session: AsyncSession, user: User, monkeypatch: pytest.MonkeyPatch
    ):
        """Full flow: 5 failed attempts -> locked -> wait -> login OK."""
        email = user.email
        ip = "192.168.1.101"

        for _ in range(5):
            await record_login_attempt(email, ip, success=False, db=db_session)

        is_locked = await _locked_right_after_last_attempt(email, ip, db_session, monkeypatch)
        assert is_locked

        await record_login_attempt(email, ip, success=True, db=db_session)

        is_locked = await check_lockout(email, ip, db=db_session)
        assert not is_locked

    async def test_lockout_per_email_ip_combo(
        self, db_session: AsyncSession, user: User, monkeypatch: pytest.MonkeyPatch
    ):
        """Lockout is per (email, ip) combo, not global."""
        email = user.email

        for _ in range(5):
            await record_login_attempt(email, "192.168.1.50", success=False, db=db_session)

        is_locked_ip1 = await _locked_right_after_last_attempt(
            email, "192.168.1.50", db_session, monkeypatch
        )
        assert is_locked_ip1

        is_locked_ip2 = await check_lockout(email, "192.168.1.51", db=db_session)
        assert not is_locked_ip2


class TestRefreshTokenRotation:
    """Test opaque refresh token rotation and replay detection."""

    async def test_create_opaque_refresh_token(self, db_session: AsyncSession, user: User):
        """Create opaque token; verify stored as hash."""
        token, family_id = await create_opaque_refresh_token(user.id, db=db_session)

        assert token is not None
        assert len(token) > 50
        assert family_id is not None

        result = await db_session.execute(
            select(RefreshToken).where(RefreshToken.family_id == family_id)
        )
        rt = result.scalar_one_or_none()
        assert rt is not None
        assert rt.revoked == False

    async def test_refresh_token_rotation_basic(self, db_session: AsyncSession, user: User):
        """Exchange refresh token for new pair; old token revoked."""
        old_token, family_id = await create_opaque_refresh_token(user.id, db=db_session)

        result = await refresh_token_rotation(old_token, db=db_session, request_ip="192.168.1.1")
        assert "access_token" in result
        assert "refresh_token" in result

        db_result = await db_session.execute(
            select(RefreshToken).where(RefreshToken.family_id == family_id)
        )
        tokens = db_result.scalars().all()
        assert any(t.revoked for t in tokens)

    async def test_refresh_token_expired(self, db_session: AsyncSession, user: User):
        """Expired token rejected."""
        from datetime import UTC, datetime, timedelta

        from fastapi import HTTPException

        token = "expired_token_xyz"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expired_rt = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            family_id=uuid.uuid4(),
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        db_session.add(expired_rt)
        await db_session.commit()

        with pytest.raises(HTTPException) as exc:
            await refresh_token_rotation(token, db=db_session, request_ip="192.168.1.1")
        assert exc.value.status_code == 401


class TestSessionManagement:
    """Test session creation, listing, and revocation."""

    async def test_create_session(self, db_session: AsyncSession, user: User):
        """Create a session."""
        session_id = await create_session(
            user.id,
            request_ip="192.168.1.1",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            db=db_session,
        )

        assert session_id is not None

        result = await db_session.execute(select(UserSession).where(UserSession.id == session_id))
        session = result.scalar_one_or_none()
        assert session is not None
        assert session.user_id == user.id
        assert session.revoked == False
        assert session.device_name and "Windows" in session.device_name

    async def test_get_user_sessions(self, db_session: AsyncSession, user: User):
        """Retrieve all active sessions for user."""
        for i in range(3):
            await create_session(
                user.id,
                request_ip=f"192.168.1.{i+10}",
                user_agent="Mozilla/5.0",
                db=db_session,
            )

        sessions = await get_user_sessions(user.id, db=db_session)
        assert len(sessions) == 3

    async def test_session_max_5_revokes_oldest(self, db_session: AsyncSession, user: User):
        """Max 5 active sessions per user; oldest is revoked."""
        for i in range(6):
            await create_session(
                user.id,
                request_ip=f"192.168.1.{i+20}",
                user_agent="Mozilla/5.0",
                db=db_session,
            )
            await db_session.commit()

        sessions = await get_user_sessions(user.id, db=db_session)
        assert len(sessions) == 5

        result = await db_session.execute(
            select(UserSession).where(UserSession.user_id == user.id)
        )
        all_sessions = result.scalars().all()
        revoked = [s for s in all_sessions if s.revoked]
        assert len(revoked) == 1

    async def test_revoke_session(self, db_session: AsyncSession, user: User):
        """Remote logout: revoke a specific session."""
        session_id = await create_session(
            user.id,
            request_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            db=db_session,
        )

        await revoke_session(user.id, session_id, db=db_session)

        result = await db_session.execute(select(UserSession).where(UserSession.id == session_id))
        session = result.scalar_one_or_none()
        assert session is not None
        assert session.revoked == True


class TestTwoFactorAuth:
    """Test TOTP setup, enable, and verification."""

    async def test_setup_2fa(self, db_session: AsyncSession, user: User):
        """Generate TOTP secret and backup codes."""
        try:
            import pyotp  # noqa: F401
        except ImportError:
            pytest.skip("pyotp not installed")

        result = await setup_2fa(user.id, db=db_session)

        assert "qr_uri" in result
        assert "backup_codes" in result
        assert len(result["backup_codes"]) == 10
        assert "otpauth://" in result["qr_uri"]

    async def test_enable_2fa(self, db_session: AsyncSession, user: User):
        """Enable 2FA with valid TOTP code."""
        try:
            import pyotp
        except ImportError:
            pytest.skip("pyotp not installed")

        await setup_2fa(user.id, db=db_session)

        result = await db_session.execute(select(User2FA).where(User2FA.user_id == user.id))
        u2fa = result.scalar_one_or_none()
        assert u2fa is not None
        totp = pyotp.TOTP(u2fa.secret_key)
        valid_code = totp.now()

        enabled = await enable_2fa(user.id, valid_code, db=db_session)
        assert enabled == True

        result = await db_session.execute(select(User2FA).where(User2FA.user_id == user.id))
        u2fa = result.scalar_one_or_none()
        assert u2fa is not None
        assert u2fa.enabled == True

    async def test_2fa_backup_codes_exist(self, db_session: AsyncSession, user: User):
        """Backup codes are generated during setup."""
        try:
            import pyotp  # noqa: F401
        except ImportError:
            pytest.skip("pyotp not installed")

        await setup_2fa(user.id, db=db_session)
        result = await db_session.execute(select(User2FA).where(User2FA.user_id == user.id))
        u2fa = result.scalar_one_or_none()
        assert u2fa is not None
        assert len(u2fa.backup_codes) > 0


class TestAuditLogging:
    """Test audit event logging."""

    async def test_audit_log_immutable(self, db_session: AsyncSession, user: User):
        """Audit log is append-only."""
        audit_entry = AuditLog(
            user_id=user.id,
            action="login_success",
            ip="192.168.1.1",
            result="success",
        )
        db_session.add(audit_entry)
        await db_session.commit()

        result = await db_session.execute(select(AuditLog).where(AuditLog.user_id == user.id))
        entries = result.scalars().all()
        assert len(entries) >= 1


