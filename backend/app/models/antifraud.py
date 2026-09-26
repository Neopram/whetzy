"""Anti-fraud models for referral and credit system (29.5)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db import Base


class DeviceFingerprint(Base):
    """Hashed device+IP record for referral activation rate limiting."""

    __tablename__ = "device_fingerprints"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    fingerprint_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    ip_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_device_fp_hash_created", "fingerprint_hash", "created_at"),
        Index("ix_device_ip_hash_created", "ip_hash", "created_at"),
    )


class FraudReviewQueue(Base):
    """Referrers flagged for manual review (velocity > 5/week)."""

    __tablename__ = "fraud_review_queue"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    referrer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    activation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
