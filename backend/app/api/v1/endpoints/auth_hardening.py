"""Auth hardening endpoints: session management, 2FA setup, audit."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import (
    enable_2fa,
    get_current_user,
    get_user_sessions,
    revoke_session,
    setup_2fa,
    verify_2fa,
)
from app.models.user import User

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
    backup_codes: list[str]


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
        return Setup2FAResponse(qr_uri=result["qr_uri"], backup_codes=result["backup_codes"])
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

