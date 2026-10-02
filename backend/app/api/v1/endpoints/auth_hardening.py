"""Auth hardening endpoints: session management, 2FA setup, audit."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import (
    check_lockout,
    disable_2fa,
    enable_2fa,
    get_current_user,
    get_user_sessions,
    record_login_attempt,
    revoke_session,
    setup_2fa,
    user_has_2fa,
    verify_2fa,
    verify_token,
)
from app.models.user import User
from app.schemas.user import Token

router = APIRouter()


# --------------------------------------------------------------------------
# Request/Response Models
# --------------------------------------------------------------------------
class SessionResponse(BaseModel):
    """Active user session."""

    id: str
    device_name: str | None
    ip: str
    created_at: str
    last_activity: str

    class Config:
        from_attributes = True


class Setup2FAResponse(BaseModel):
    """2FA setup response with QR code and backup codes."""

    qr_uri: str
    # El mismo QR dibujado en SVG (el frontend no carga una librería para eso)
    # y el secreto para quien prefiera teclearlo en su app.
    qr_svg: str
    secret: str
    backup_codes: list[str]


class Login2FARequest(BaseModel):
    """Segundo paso del login: el código, y el token del primero (o su cookie)."""

    code: str = Field(min_length=6, max_length=8)
    mfa_token: str | None = None


class Status2FAResponse(BaseModel):
    enabled: bool
    backup_codes_left: int


class Enable2FARequest(BaseModel):
    """Enable 2FA with TOTP code."""

    totp_code: str = Field(min_length=6, max_length=6)


class Verify2FARequest(BaseModel):
    """Verify 2FA with TOTP or backup code."""

    code: str = Field(min_length=6, max_length=8)


# --------------------------------------------------------------------------
# Session Endpoints
# --------------------------------------------------------------------------
@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SessionResponse]:
    """Get all active sessions for current user."""
    sessions = await get_user_sessions(current_user.id, db=db)

    return [
        SessionResponse(
            id=str(session.id),
            device_name=session.device_name,
            ip=session.ip,
            created_at=session.created_at.isoformat(),
            last_activity=session.last_activity.isoformat(),
        )
        for session in sessions
    ]


@router.post("/sessions/{session_id}/revoke", status_code=status.HTTP_200_OK)
async def revoke_user_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Remote logout: revoke a specific session."""
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID")

    await revoke_session(current_user.id, sid, db=db)
    return {"message": "Session revoked successfully"}


# --------------------------------------------------------------------------
# 2FA Endpoints
# --------------------------------------------------------------------------
@router.post("/2fa/setup", response_model=Setup2FAResponse)
async def setup_2fa_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Setup2FAResponse:
    """Initialize 2FA setup; return QR code and backup codes.

    User must print/save backup codes and confirm TOTP before enabling.
    """
    try:
        result = await setup_2fa(current_user.id, db=db)
        return Setup2FAResponse(
            qr_uri=result["qr_uri"],
            qr_svg=_qr_svg(result["qr_uri"]),
            secret=result["secret"],
            backup_codes=result["backup_codes"],
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/2fa/enable", status_code=status.HTTP_200_OK)
async def enable_2fa_endpoint(
    payload: Enable2FARequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Confirm TOTP code and enable 2FA."""
    try:
        enabled = await enable_2fa(current_user.id, payload.totp_code, db=db)
        if not enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid TOTP code; please try again",
            )
        return {"message": "2FA enabled successfully"}
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/2fa/verify", status_code=status.HTTP_200_OK)
async def verify_2fa_endpoint(
    payload: Verify2FARequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Verify TOTP or backup code (for login flow)."""
    try:
        verified = await verify_2fa(current_user.id, payload.code, db=db)
        if not verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid code; please try again",
            )
        return {"message": "2FA verified"}
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



def _qr_svg(data: str) -> str:
    """QR en SVG con `qrcode`, que ya es dependencia del backend."""
    import io

    import qrcode
    import qrcode.image.svg

    img = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathImage, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode("utf-8")


@router.get("/2fa/status", response_model=Status2FAResponse)
async def status_2fa_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Status2FAResponse:
    from sqlalchemy import select

    from app.models.auth import User2FA

    u2fa = (
        await db.execute(select(User2FA).where(User2FA.user_id == current_user.id))
    ).scalar_one_or_none()
    enabled = bool(u2fa and u2fa.enabled)
    return Status2FAResponse(
        enabled=enabled, backup_codes_left=len(u2fa.backup_codes) if enabled and u2fa else 0
    )


@router.post("/2fa/disable", status_code=status.HTTP_200_OK)
async def disable_2fa_endpoint(
    payload: Verify2FARequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Desactivar exige un código (TOTP o de respaldo): una sesión robada no basta."""
    if not await disable_2fa(current_user.id, payload.code, db=db):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_code")
    return {"enabled": False}


@router.post("/2fa/login", response_model=Token)
async def login_2fa_endpoint(
    payload: Login2FARequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Segundo paso del login con 2FA. El token del primer paso llega en el
    cuerpo (contraseña) o en la cookie `whetzy_mfa` (OAuth). Cada código
    erróneo cuenta como intento fallido para el bloqueo progresivo."""
    from app.api.v1.endpoints.auth import complete_login
    from app.core.cookies import MFA_COOKIE, clear_mfa_cookie

    raw = payload.mfa_token or request.cookies.get(MFA_COOKIE)
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="mfa_token_missing")
    token_data = verify_token(raw, expected_type="mfa")
    try:
        user_id = uuid.UUID(str(token_data.sub))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="mfa_token_invalid")
    user = await db.get(User, user_id)
    if user is None or not user.is_active or token_data.jvs != user.jwt_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="mfa_token_invalid")

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    if await check_lockout(user.email, client_ip, db):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to too many failed login attempts",
        )
    if not await user_has_2fa(user.id, db) or not await verify_2fa(user.id, payload.code, db=db):
        await record_login_attempt(user.email, client_ip, False, db)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_code")

    clear_mfa_cookie(response)
    return await complete_login(user, user.email, client_ip, user_agent, response, db)
