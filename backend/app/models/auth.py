"""Auth security models: login attempts, refresh tokens, sessions, 2FA, audit logging."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db import Base


class LoginAttempt(Base):
    """Track login attempts per (email, ip) for progressive lockout."""

    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ip: Mapped[str] = mapped_column(String(45), nullable=False, index=True)  # IPv4 + IPv6
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class RefreshToken(Base):
    """Opaque refresh tokens stored in DB for rotation & replay detection."""

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    family_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)  # Tracks token family
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)


class UserSession(Base):
    """Track active user sessions with device fingerprinting."""

    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fingerprint: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # SHA256(user_agent + ip)
    ip: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[str] = mapped_column(Text, nullable=False)
    device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)


class User2FA(Base):
    """Two-factor authentication TOTP setup per user."""

    __tablename__ = "user_2fa"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    secret_key: Mapped[str] = mapped_column(String(32), nullable=False)  # Base32-encoded TOTP secret
    backup_codes: Mapped[list[str]] = mapped_column(
        JSON(), nullable=False, server_default="[]"
    )  # Array of hashed one-time codes
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_used: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    """Immutable append-only security audit log."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[str] = mapped_column(String(16), default="success", nullable=False)  # success, failed, blocked
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

