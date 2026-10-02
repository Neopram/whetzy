"""JWT authentication: token creation/verification, password hashing,
and the `get_current_user` FastAPI dependency.
Also includes auth hardening: lockout, refresh rotation, sessions, 2FA, audit logging.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.models.user import User
from app.schemas.user import TokenPayload

logger = logging.getLogger("whetzy.security")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dummy hash for constant-time comparison when no user is found (ASVS V2.2 timing attack).
_DUMMY_HASH = pwd_context.hash("dummy-password-for-timing-safety")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)

TokenType = Literal["access", "refresh", "unsubscribe", "mfa"]


# --------------------------------------------------------------------------
# Password hashing
# --------------------------------------------------------------------------
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# --------------------------------------------------------------------------
# Token creation
# --------------------------------------------------------------------------
def _signing_config() -> tuple[str, str]:
    """Return (key, algorithm) for signing new tokens.

    Uses RS256 when JWT_PRIVATE_KEY is configured, falls back to HS256.
    """
    if settings.JWT_PRIVATE_KEY:
        return settings.JWT_PRIVATE_KEY, "RS256"
    return settings.SECRET_KEY, settings.JWT_ALGORITHM


def _create_token(
    subject: str | uuid.UUID,
    token_type: TokenType,
    expires_delta: timedelta,
    jwt_version: int = 1,
) -> str:
    now = datetime.now(UTC)
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": now + expires_delta,
        "jvs": jwt_version,
    }
    key, algorithm = _signing_config()
    return jwt.encode(to_encode, key, algorithm=algorithm)


def create_access_token(
    subject: str | uuid.UUID,
    expires_delta: timedelta | None = None,
    jwt_version: int = 1,
) -> str:
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(subject, "access", delta, jwt_version)


def create_unsubscribe_token(subject: str | uuid.UUID) -> str:
    """Token del enlace «darse de baja» de los correos de marketing. Su tipo
    no sirve de sesión: `verify_token` exige el tipo esperado. Dura más que
    cualquier correo que lo lleve."""
    return _create_token(subject, "unsubscribe", timedelta(days=400))


def create_mfa_token(subject: str | uuid.UUID, jwt_version: int = 1) -> str:
    """Segundo paso del login con 2FA: prueba que la contraseña fue correcta,
    vale 5 minutos y solo sirve en `POST /auth/2fa/login` junto a un código.
    No es una sesión: `verify_token` exige el tipo esperado."""
    return _create_token(subject, "mfa", timedelta(minutes=5), jwt_version)


def create_refresh_token(
    subject: str | uuid.UUID,
    expires_delta: timedelta | None = None,
    jwt_version: int = 1,
) -> str:
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(subject, "refresh", delta, jwt_version)


# --------------------------------------------------------------------------
# Token verification
# --------------------------------------------------------------------------
def _verification_keys() -> list[tuple[str, list[str]]]:
    """Return ordered list of (key, algorithms) to try when verifying.

    RS256 first (if configured), then HS256 fallback for pre-migration tokens.
    """
    keys: list[tuple[str, list[str]]] = []
    if settings.JWT_PUBLIC_KEY:
        keys.append((settings.JWT_PUBLIC_KEY, ["RS256"]))
    keys.append((settings.SECRET_KEY, [settings.JWT_ALGORITHM]))
    return keys


def verify_token(token: str, expected_type: TokenType = "access") -> TokenPayload:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = None
    for key, algorithms in _verification_keys():
        try:
            payload = jwt.decode(token, key, algorithms=algorithms)
            break
        except JWTError:
            continue

    if payload is None:
        raise credentials_exception

    token_data = TokenPayload(**payload)
    if token_data.sub is None or token_data.type != expected_type:
        raise credentials_exception
    return token_data


# --------------------------------------------------------------------------
# FastAPI dependencies
# --------------------------------------------------------------------------
async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    from app.core.cookies import ACCESS_COOKIE

    if token is None:
        token = request.cookies.get(ACCESS_COOKIE)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = verify_token(token, expected_type="access")

    try:
        user_id = uuid.UUID(token_data.sub)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        ) from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    # Reject tokens issued before a password change/reset (ASVS V3.3).
    token_jvs = getattr(token_data, "jvs", None)
    if token_jvs is not None and int(token_jvs) != user.jwt_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user



async def get_optional_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """El usuario si la petición trae una sesión válida; None si no.

    Para endpoints públicos que solo cambian algo cuando sabemos quién pide (el
    cupo Free de lecciones, 39.4). Un token caducado o revocado no convierte una
    lectura pública en un 401: se trata como anónimo.
    """
    try:
        return await get_current_user(request, token, db)
    except HTTPException:
        return None

async def get_current_active_premium_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires a premium subscription",
        )
    return current_user


# --------------------------------------------------------------------------
# Progressive Account Lockout
# --------------------------------------------------------------------------
def _as_utc(value: datetime) -> datetime:
    """Devuelve el datetime en UTC aware.

    Postgres guarda `TIMESTAMPTZ` y asyncpg lo devuelve aware, pero SQLite (la
    suite de tests) y cualquier fila escrita sin zona lo devuelven naive:
    compararlos con `datetime.now(UTC)` reventaba con
    `TypeError: can't compare offset-naive and offset-aware datetimes`.
    """
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


async def check_lockout(email: str, ip: str, db: AsyncSession) -> bool:
    """Check if (email, ip) combo is locked out. Returns True if locked."""
    from app.models.auth import LoginAttempt

    result = await db.execute(
        select(LoginAttempt).where(
            LoginAttempt.email == email,
            LoginAttempt.ip == ip,
            LoginAttempt.success == False,
            LoginAttempt.created_at > datetime.now(UTC) - timedelta(minutes=15),
        ).order_by(LoginAttempt.created_at.desc())
    )
    attempts = result.scalars().all()

    if len(attempts) < 5:
        return False  # Not locked out

    # Calculate delay: 5 attempts -> 1s, 6 -> 2s, 7 -> 4s, etc.
    delay_seconds = 2 ** (len(attempts) - 5)
    time_since_last = (datetime.now(UTC) - _as_utc(attempts[0].created_at)).total_seconds()

    return bool(time_since_last < delay_seconds)


async def record_login_attempt(email: str, ip: str, success: bool, db: AsyncSession) -> None:
    """Record login attempt; reset lockout on success."""
    from app.models.auth import LoginAttempt

    db.add(LoginAttempt(email=email, ip=ip, success=success))
    await db.commit()

    if success:
        # Clear old failed attempts for this combo
        result = await db.execute(
            select(LoginAttempt).where(
                LoginAttempt.email == email,
                LoginAttempt.ip == ip,
                LoginAttempt.success == False,
            )
        )
        for attempt in result.scalars().all():
            await db.delete(attempt)
        await db.commit()


# --------------------------------------------------------------------------
# Refresh Token Rotation
# --------------------------------------------------------------------------
async def create_opaque_refresh_token(user_id: uuid.UUID, db: AsyncSession) -> tuple[str, uuid.UUID]:
    """Create opaque refresh token; store hash in DB. Returns (token, family_id)."""
    from app.models.auth import RefreshToken

    token = secrets.token_urlsafe(64)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    family_id = uuid.uuid4()

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        family_id=family_id,
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    db.add(refresh_token)
    await db.commit()

    return token, family_id


async def verify_opaque_refresh_token(token: str, db: AsyncSession) -> dict[str, Any]:
    """Verify opaque refresh token; detect replays. Returns {user_id, family_id}."""
    from app.models.auth import RefreshToken

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    rt = result.scalar_one_or_none()

    if not rt or rt.revoked or _as_utc(rt.expires_at) < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    return {"user_id": rt.user_id, "family_id": rt.family_id}


async def refresh_token_rotation(
    token: str,
    db: AsyncSession,
    request_ip: str | None = None,
) -> dict[str, str]:
    """Exchange refresh token for new access + refresh token pair.

    Detects replay attacks using family_id tracking.
    Returns {access_token, refresh_token}.
    """
    from app.models.auth import RefreshToken

    # 1. Verify & get user_id, family_id
    payload = await verify_opaque_refresh_token(token, db)
    user_id = payload["user_id"]
    family_id = payload["family_id"]

    # 2. Check for replays in same family
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.family_id == family_id,
            RefreshToken.user_id == user_id,
            RefreshToken.issued_at > datetime.now(UTC) - timedelta(minutes=5),
        )
    )
    replays = result.scalars().all()

    if len(replays) > 1:
        # Replay detected: revoke entire family
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.family_id == family_id)
        )
        for rt in result.scalars().all():
            rt.revoked = True
        await db.commit()

        # Alert user
        await log_audit_event(
            user_id,
            "refresh_replay_attack",
            ip=request_ip,
            result="blocked",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token replay detected; session revoked",
        )

    # 3. Issue new token pair (new opaque refresh, same family)
    new_access = create_access_token(user_id)
    new_refresh_token, _ = await create_opaque_refresh_token(user_id, db)

    # 4. Mark old token as used (revoke)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    old_token = result.scalar_one_or_none()
    if old_token:
        old_token.revoked = True
        await db.commit()

    await log_audit_event(user_id, "refresh_token_issued", ip=request_ip)

    return {"access_token": new_access, "refresh_token": new_refresh_token}


# --------------------------------------------------------------------------
# Session Management
# --------------------------------------------------------------------------
async def create_session(
    user_id: uuid.UUID,
    request_ip: str,
    user_agent: str,
    db: AsyncSession,
) -> uuid.UUID:
    """Create new session; limit to max 5 per user.

    Revokes oldest session if limit exceeded.
    Returns session_id.
    """
    from app.models.auth import UserSession

    fingerprint = hashlib.sha256(f"{user_agent}{request_ip}".encode()).hexdigest()

    # Check active sessions
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked == False,
            UserSession.last_activity > datetime.now(UTC) - timedelta(days=30),
        )
    )
    active = result.scalars().all()

    if len(active) >= 5:
        # Revoke oldest session
        oldest = min(active, key=lambda s: s.last_activity)
        oldest.revoked = True
        await db.commit()
        await log_audit_event(
            user_id,
            "session_evoked",
            ip=oldest.ip,
            metadata={"evicted_session_id": str(oldest.id)},
            db=db,
        )

    session = UserSession(
        user_id=user_id,
        fingerprint=fingerprint,
        ip=request_ip,
        user_agent=user_agent,
        device_name=parse_user_agent(user_agent),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    await log_audit_event(
        user_id,
        "session_created",
        ip=request_ip,
        user_agent=user_agent,
        metadata={"session_id": str(session.id)},
        db=db,
    )

    return session.id


async def get_user_sessions(user_id: uuid.UUID, db: AsyncSession) -> list[Any]:
    """Get all active sessions for user (not revoked, within 30-day inactivity)."""
    from app.models.auth import UserSession

    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked == False,
        ).order_by(UserSession.last_activity.desc())
    )
    return list(result.scalars().all())


async def revoke_session(
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Remote logout: revoke session."""
    from app.models.auth import UserSession

    result = await db.execute(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    session.revoked = True
    await db.commit()
    await log_audit_event(
        user_id,
        "session_revoked",
        ip=session.ip,
        metadata={"session_id": str(session.id)},
        db=db,
    )


# --------------------------------------------------------------------------
# Two-Factor Authentication (TOTP)
# --------------------------------------------------------------------------
async def user_has_2fa(user_id: uuid.UUID, db: AsyncSession) -> bool:
    """True si el usuario tiene la verificación en dos pasos activada."""
    from app.models.auth import User2FA

    result = await db.execute(
        select(User2FA.enabled).where(User2FA.user_id == user_id)
    )
    return bool(result.scalar())


async def disable_2fa(user_id: uuid.UUID, code: str, db: AsyncSession) -> bool:
    """Desactiva la 2FA con un código válido (TOTP o de respaldo)."""
    from app.models.auth import User2FA

    if not await verify_2fa(user_id, code, db=db):
        return False
    result = await db.execute(select(User2FA).where(User2FA.user_id == user_id))
    u2fa = result.scalar_one_or_none()
    if u2fa is not None:
        await db.delete(u2fa)
        await db.commit()
    await log_audit_event(user_id, "2fa_disabled")
    return True


async def setup_2fa(user_id: uuid.UUID, db: AsyncSession) -> dict[str, Any]:
    """Generate TOTP secret and backup codes for 2FA setup.

    Returns {qr_uri, backup_codes}.
    Caller must print backup codes to user (never send via email/SMS).
    """
    try:
        import pyotp
    except ImportError:
        raise RuntimeError("pyotp not installed; 2FA unavailable")

    from app.models.auth import User2FA

    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)

    # Get user email for QR code
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    qr_uri = totp.provisioning_uri(name=user.email, issuer_name="Whetzy")

    # Generate 10 one-time backup codes
    backup_codes = [secrets.token_hex(4) for _ in range(10)]
    backup_codes_hash = [hashlib.sha256(code.encode()).hexdigest() for code in backup_codes]

    # Check if 2FA already setup
    result = await db.execute(select(User2FA).where(User2FA.user_id == user_id))
    existing_2fa = result.scalar_one_or_none()
    if existing_2fa is not None and existing_2fa.enabled:
        # Rehacer el alta pondría `enabled=False`: con una sesión robada se
        # apagaría la 2FA sin código. Para cambiarla, primero se desactiva con uno.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="2fa_already_enabled")

    if existing_2fa:
        # Update existing 2FA (disabled state)
        existing_2fa.secret_key = secret  # type: ignore[attr-defined]
        existing_2fa.backup_codes = backup_codes_hash  # type: ignore[attr-defined]
        existing_2fa.enabled = False  # type: ignore[attr-defined]
    else:
        # Create new 2FA record
        u2fa = User2FA(
            user_id=user_id,
            secret_key=secret,
            backup_codes=backup_codes_hash,
            enabled=False,
        )
        db.add(u2fa)

    await db.commit()

    return {
        "qr_uri": qr_uri,
        "secret": secret,
        "backup_codes": backup_codes,
    }


async def enable_2fa(user_id: uuid.UUID, totp_code: str, db: AsyncSession) -> bool:
    """Verify TOTP code and enable 2FA."""
    try:
        import pyotp
    except ImportError:
        raise RuntimeError("pyotp not installed; 2FA unavailable")

    from app.models.auth import User2FA

    result = await db.execute(select(User2FA).where(User2FA.user_id == user_id))
    u2fa = result.scalar_one_or_none()

    if not u2fa:
        return False

    totp = pyotp.TOTP(u2fa.secret_key)

    if not totp.verify(totp_code, valid_window=1):
        return False

    u2fa.enabled = True
    await db.commit()
    await log_audit_event(user_id, "2fa_enabled")

    return True


async def verify_2fa(
    user_id: uuid.UUID,
    totp_code: str,
    db: AsyncSession,
) -> bool:
    """Verify TOTP code or backup code.

    Returns True if valid.
    Backup codes are one-time use (removed on success).
    """
    try:
        import pyotp
    except ImportError:
        raise RuntimeError("pyotp not installed; 2FA unavailable")

    from app.models.auth import User2FA

    result = await db.execute(select(User2FA).where(User2FA.user_id == user_id))
    u2fa = result.scalar_one_or_none()

    if not u2fa or not u2fa.enabled:
        return False

    totp = pyotp.TOTP(u2fa.secret_key)

    # Try TOTP first
    if totp.verify(totp_code, valid_window=1):
        u2fa.last_used = datetime.now(UTC)
        await db.commit()
        return True

    # Try backup code
    code_hash = hashlib.sha256(totp_code.encode()).hexdigest()
    if code_hash in u2fa.backup_codes:
        # One-time use: remove from list
        remaining = [c for c in u2fa.backup_codes if c != code_hash]
        u2fa.backup_codes = remaining
        u2fa.last_used = datetime.now(UTC)
        await db.commit()
        await log_audit_event(user_id, "2fa_backup_code_used")
        return True

    return False


# --------------------------------------------------------------------------
# Audit Logging
# --------------------------------------------------------------------------
async def log_audit_event(
    user_id: uuid.UUID | None,
    action: str,
    ip: str | None = None,
    user_agent: str | None = None,
    result: str = "success",
    error_message: str | None = None,
    metadata: dict[str, Any] | None = None,
    db: AsyncSession | None = None,
) -> None:
    """Log security-relevant action; immutable append-only.

    No interrumpe el flujo principal si falla, pero deja el error en el log
    (`whetzy.security`). Usa la sesion recibida si la hay.
    """
    from app.models.auth import AuditLog

    try:
        if db is not None:
            audit_entry = AuditLog(
                user_id=user_id,
                action=action,
                ip=ip,
                user_agent=user_agent,
                result=result,
                error_message=error_message,
                event_data=metadata,
            )
            db.add(audit_entry)
            await db.commit()
        else:
            from app.core.db import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                audit_entry = AuditLog(
                    user_id=user_id,
                    action=action,
                    ip=ip,
                    user_agent=user_agent,
                    result=result,
                    error_message=error_message,
                    event_data=metadata,
                )
                session.add(audit_entry)
                await session.commit()
    except Exception:
        # El audit log no puede tumbar el flujo principal, pero tampoco puede
        # desaparecer en silencio: es una pieza de cumplimiento (22.3).
        logger.exception("audit log failed: action=%s result=%s", action, result)


# --------------------------------------------------------------------------
# Utility Functions
# --------------------------------------------------------------------------
def parse_user_agent(user_agent: str) -> str:
    """Parse user agent into device name (e.g., 'Chrome on Windows')."""
    if not user_agent:
        return "Unknown"

    # Simple parsing; could use user-agents library for more detail
    if "Windows" in user_agent:
        os_name = "Windows"
    elif "Macintosh" in user_agent or "Mac OS" in user_agent:
        os_name = "macOS"
    elif "Linux" in user_agent:
        os_name = "Linux"
    elif "iPhone" in user_agent:
        os_name = "iOS"
    elif "Android" in user_agent:
        os_name = "Android"
    else:
        os_name = "Unknown"

    if "Chrome" in user_agent:
        browser = "Chrome"
    elif "Safari" in user_agent:
        browser = "Safari"
    elif "Firefox" in user_agent:
        browser = "Firefox"
    elif "Edge" in user_agent:
        browser = "Edge"
    else:
        browser = "Unknown"

    return f"{browser} on {os_name}"










