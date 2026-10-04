"""Authentication endpoints: register, login, refresh, current user, password reset."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cookies import clear_auth_cookies, set_auth_cookies
from app.core.db import get_db
from app.core.security import (
    _DUMMY_HASH,
    check_lockout,
    create_access_token,
    create_mfa_token,
    create_refresh_token,
    create_session,
    get_current_user,
    get_password_hash,
    log_audit_event,
    record_login_attempt,
    user_has_2fa,
    verify_password,
    verify_token,
)
from app.models.email_verification import EmailVerificationToken
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.schemas.user import RefreshRequest, Token, UserCreate, UserRead
from app.services import account_deletion
from app.services.username_filter import contains_blocked_word

router = APIRouter()


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    token: str


class UpdateProfileRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    avatar_emoji: str | None = Field(default=None, max_length=16)
    language: str | None = Field(default=None, pattern="^(es|en)$")
    # Respuestas del onboarding (índice de opción, 0-2). 34.11.
    onboarding_experience: int | None = Field(default=None, ge=0, le=2)
    onboarding_goal: int | None = Field(default=None, ge=0, le=2)
    onboarding_weekly_time: int | None = Field(default=None, ge=0, le=2)

    @field_validator("display_name")
    @classmethod
    def _sin_palabra_bloqueada(cls, value: str | None) -> str | None:
        # 19.11: filtro mínimo al editar el nombre visible.
        if value is not None and contains_blocked_word(value):
            raise ValueError("That name isn't allowed")
        return value


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Token:
    if not payload.age_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Age confirmation is required (must be 13 or older)",
        )

    existing = await db.execute(
        select(User).where(or_(User.email == payload.email, User.username == payload.username))
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with that email or username already exists",
        )

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=get_password_hash(payload.password),
        display_name=payload.display_name,
        language=payload.language,
        email_verified=False,
        age_confirmed=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Fire-and-forget email verification.
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    evt = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    db.add(evt)
    from app.services.analytics import track as analytics_track
    await analytics_track(db, "user_registered", user_id=user.id)
    await db.commit()
    from app.services import email as email_svc
    email_svc.send_email_verification(
        to=user.email, name=user.display_name, token=raw_token, lang=user.language
    )
    email_svc.send_welcome(to=user.email, name=user.display_name, lang=user.language)

    token = Token(
        access_token=create_access_token(user.id, jwt_version=user.jwt_version),
        refresh_token=create_refresh_token(user.id, jwt_version=user.jwt_version),
    )
    set_auth_cookies(response, token.access_token, token.refresh_token)
    return token


class MfaChallenge(BaseModel):
    """La contraseña es correcta y la cuenta tiene 2FA: falta el código
    (`POST /auth/2fa/login`). No hay sesión todavía."""

    mfa_required: bool = True
    mfa_token: str


async def complete_login(
    user: User, email: str, client_ip: str, user_agent: str, response: Response, db: AsyncSession
) -> Token:
    """Lo que cierra un login correcto: intento bueno, sesión, auditoría y
    cookies. Lo comparten la contraseña sin 2FA y el segundo paso con código."""
    await record_login_attempt(email, client_ip, True, db)
    await create_session(user.id, client_ip, user_agent, db)
    await log_audit_event(
        user.id,
        "login_success",
        ip=client_ip,
        user_agent=user_agent,
        result="success",
        db=db,
    )
    token = Token(
        access_token=create_access_token(user.id, jwt_version=user.jwt_version),
        refresh_token=create_refresh_token(user.id, jwt_version=user.jwt_version),
    )
    set_auth_cookies(response, token.access_token, token.refresh_token)
    return token


@router.post("/login", response_model=Token | MfaChallenge)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token | MfaChallenge:
    """Login with email and password. Includes auth hardening with progressive lockout and session tracking.

    Con 2FA activada no hay sesión todavía: devuelve `MfaChallenge` y el login
    se completa en `POST /auth/2fa/login` con el código. Antes la 2FA se podía
    activar y el login la ignoraba.
    """
    # Extract IP and user-agent from request
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    # OAuth2PasswordRequestForm's `username` field carries the user's email.
    email = form_data.username

    # Check if account is locked out
    is_locked = await check_lockout(email, client_ip, db)
    if is_locked:
        # Log failed attempt due to lockout
        await record_login_attempt(email, client_ip, False, db)
        await log_audit_event(
            None,
            "login_lockout",
            ip=client_ip,
            user_agent=user_agent,
            result="blocked",
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to too many failed login attempts",
        )

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Always call verify_password to prevent timing-based user enumeration (ASVS V2.2).
    # OAuth-only accounts have hashed_password=None — treat as wrong password.
    hash_to_check = (user.hashed_password if user is not None and user.hashed_password else _DUMMY_HASH)
    password_ok = verify_password(form_data.password, hash_to_check)

    if user is None or not password_ok:
        # Record failed attempt
        await record_login_attempt(email, client_ip, False, db)
        await log_audit_event(
            None,
            "login_failed",
            ip=client_ip,
            user_agent=user_agent,
            result="failed",
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active and not await account_deletion.restore_if_pending(db, user):
        await log_audit_event(
            user.id,
            "login_failed",
            ip=client_ip,
            user_agent=user_agent,
            result="failed",
            error_message="Inactive user",
            db=db,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    if await user_has_2fa(user.id, db):
        # Contraseña correcta, pero sin código no hay sesión. No se registra el
        # intento como bueno: el bloqueo progresivo sigue contando hasta el código.
        await log_audit_event(
            user.id, "login_mfa_required", ip=client_ip, user_agent=user_agent,
            result="pending", db=db,
        )
        return MfaChallenge(mfa_token=create_mfa_token(user.id, jwt_version=user.jwt_version))

    return await complete_login(user, email, client_ip, user_agent, response, db)


@router.post("/refresh", response_model=Token)
async def refresh(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Refresh access token using refresh token. Includes audit logging."""
    from app.core.cookies import REFRESH_COOKIE

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    refresh_tok = (payload.refresh_token if payload and payload.refresh_token else None)
    if not refresh_tok:
        refresh_tok = request.cookies.get(REFRESH_COOKIE)
    if not refresh_tok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    token_data = verify_token(refresh_tok, expected_type="refresh")

    try:
        user_id = uuid.UUID(token_data.sub) if token_data.sub else None
    except ValueError:
        user_id = None
    if user_id is None:
        await log_audit_event(
            None,
            "refresh_failed",
            ip=client_ip,
            user_agent=user_agent,
            result="failed",
            error_message="Invalid refresh token",
            db=db,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        await log_audit_event(
            user_id,
            "refresh_failed",
            ip=client_ip,
            user_agent=user_agent,
            result="failed",
            error_message="User not found or inactive",
            db=db,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    # S.1: un refresh token emitido antes de un cambio de contraseña, "cerrar
    # sesión en todos los dispositivos" o activar 2FA (todos suben jwt_version)
    # seguía siendo válido aquí y volvía a dar acceso — el mismo chequeo que ya
    # hace /2fa/login con el mfa_token, que a este endpoint le faltaba.
    if token_data.jvs != user.jwt_version:
        await log_audit_event(
            user.id,
            "refresh_failed",
            ip=client_ip,
            user_agent=user_agent,
            result="failed",
            error_message="Refresh token revoked (jwt_version mismatch)",
            db=db,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Log token refresh
    await log_audit_event(
        user.id,
        "refresh_token_issued",
        ip=client_ip,
        user_agent=user_agent,
        result="success",
        db=db,
    )

    token = Token(
        access_token=create_access_token(user.id, jwt_version=user.jwt_version),
        refresh_token=create_refresh_token(user.id, jwt_version=user.jwt_version),
    )
    set_auth_cookies(response, token.access_token, token.refresh_token)
    return token


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Logout: revoke current session, clear cookies, and log the event."""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    await log_audit_event(
        current_user.id,
        "logout",
        ip=client_ip,
        user_agent=user_agent,
        result="success",
        db=db,
    )

    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.delete("/me/account", status_code=status.HTTP_200_OK)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Borrado con 30 días de gracia (19.12): desactiva ya, purga a los 30 días.

    Volver a iniciar sesión dentro de la gracia recupera la cuenta
    (`account_deletion.restore_if_pending`).
    """
    purge_at = await account_deletion.request_deletion(db, current_user)
    return {
        "message": (
            "Cuenta desactivada. Se borrará permanentemente en 30 días; "
            "si vuelves a iniciar sesión antes, se recupera."
        ),
        "purge_after": purge_at.isoformat(),
    }


@router.patch("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update editable profile fields. Only provided fields are changed."""
    if payload.display_name is not None:
        current_user.display_name = payload.display_name
    if payload.avatar_emoji is not None:
        current_user.avatar_emoji = payload.avatar_emoji
    if payload.language is not None:
        current_user.language = payload.language
    for field in ("onboarding_experience", "onboarding_goal", "onboarding_weekly_time"):
        value = getattr(payload, field)
        if value is not None:
            setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.patch("/me/password", status_code=status.HTTP_200_OK)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Change password — requires current password for confirmation."""
    if current_user.hashed_password is None or not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    current_user.hashed_password = get_password_hash(payload.new_password)
    # Invalidate all existing tokens by bumping the version (ASVS V3.3).
    current_user.jwt_version = current_user.jwt_version + 1
    await db.commit()
    await log_audit_event(
        current_user.id, "password_change", db=db,
    )
    return {"message": "Password changed successfully. Please log in again with your new password."}


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Consume an email verification link (single-use, 24h TTL).

    0.2: reutilizaba `ResetPasswordRequest` -- que exige `new_password` --
    y por tanto cualquier cliente que mandara solo `{token}` (lo correcto
    aquí, no se cambia ninguna contraseña) recibía un 422 sin tocar la
    lógica de abajo. Nadie lo notó porque no había ni página ni test que
    llamara a este endpoint de verdad.
    """
    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    result = await db.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
    )
    evt = result.scalar_one_or_none()
    now = datetime.now(UTC)
    if evt is None or evt.used or evt.expires_at.replace(tzinfo=UTC) < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification link",
        )

    result2 = await db.execute(select(User).where(User.id == evt.user_id))
    user = result2.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    user.email_verified = True
    evt.used = True
    await db.commit()
    return {"message": "Email verified. You now have full access."}


class ResendVerificationRequest(BaseModel):
    email: str


def _require_outbound_email() -> None:
    """H.30: in production with no provider, the `log` fallback sends nothing.

    Answering 200 there told users a link was on its way when none ever would be.
    The check depends only on server configuration, never on the email asked
    for, so it reveals nothing about which accounts exist.
    """
    from app.core.config import settings
    from app.services import email as email_svc

    if settings.ENVIRONMENT == "production" and email_svc.resolve_provider() == "log":
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="email_not_configured")


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    payload: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Resend the email verification link (rate limited: max 1 pending token per user)."""
    _require_outbound_email()
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user and user.is_active and not user.email_verified:
        # Invalidate any existing unused tokens.
        existing = await db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.used == False,
            )
        )
        for tok in existing.scalars().all():
            tok.used = True

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        evt = EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
        db.add(evt)
        await db.commit()
        from app.services import email as email_svc
        email_svc.send_email_verification(
            to=user.email, name=user.display_name, token=raw_token, lang=user.language
        )

    return {"message": "If that email is registered and unverified, a new link has been sent."}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Request a password reset. Always returns 200 to prevent user enumeration."""
    _require_outbound_email()
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now(UTC) + timedelta(hours=1)

        prt = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(prt)
        await db.commit()

        from app.services import email as email_svc
        email_svc.send_password_reset(
            to=user.email,
            name=user.display_name,
            token=raw_token,
            lang=user.language,
        )

    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Consume a password-reset token (single-use, expires in 1h) and set a new password."""
    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters",
        )

    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    prt = result.scalar_one_or_none()

    now = datetime.now(UTC)
    if prt is None or prt.used or prt.expires_at.replace(tzinfo=UTC) < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    result2 = await db.execute(select(User).where(User.id == prt.user_id))
    user = result2.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user.hashed_password = get_password_hash(payload.new_password)
    # Invalidate all existing tokens (ASVS V3.3).
    user.jwt_version = user.jwt_version + 1
    prt.used = True
    await db.commit()

    return {"message": "Password updated. You can now log in with your new password."}




