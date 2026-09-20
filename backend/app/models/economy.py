"""Economy models: credit ledger, promo codes, referral tracking."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db import Base


class CreditReasonEnum(str, Enum):
    """Reasons for credit transactions."""
    # Grifos (earning)
    MODULE_DONE = "module_done"
    STREAK_7 = "streak_7"
    STREAK_30 = "streak_30"
    PROJECT_DELIVERED = "project_delivered"
    SKILL_SKIPPED = "skill_skipped"
    MOCK_PASSED = "mock_passed"
    REFERRAL_ACTIVATED = "referral_activated"
    REFERRAL_WELCOME = "referral_welcome"
    PROMO_CODE = "promo_code"
    REACTIVATION = "reactivation"
    ONBOARDING_BONUS = "onboarding_bonus"
    
    # Sumideros (spending)
    SPEND_MOCK = "spend_mock"
    SPEND_FREEZE = "spend_freeze"
    SPEND_REPORT = "spend_report"
    SPEND_BOOTCAMP = "spend_bootcamp"
    SPEND_MARKETPLACE = "spend_marketplace"
    SPEND_COMPANY_SEAT = "spend_company_seat"
    
    # Special
    EXPIRE = "expire"
    CLAWBACK = "clawback"
    ADMIN_ADJUST = "admin_adjust"


class PromoCodeTypeEnum(str, Enum):
    """Types of promo codes."""
    ONBOARDING = "onboarding"
    CAMPAIGN = "campaign"
    REACTIVATION = "reactivation"
    REFERRAL_BONUS = "referral_bonus"
    INSTRUCTOR = "instructor"


class CreditLedger(Base):
    """Immutable credit transaction ledger."""
    __tablename__ = "credit_ledger"
    
    # BigInteger como PK no autoincrementa en SQLite, que es lo que usan los
    # tests: el INSERT sale sin id y muere por NOT NULL. La variante deja
    # BIGINT en Postgres y un INTEGER (alias de rowid) en SQLite.
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(50), nullable=False)
    
    ref_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ref_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    lot_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("credit_ledger.id"), nullable=True
    )
    
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    
    __table_args__ = (
        CheckConstraint("amount != 0", name="ck_credit_nonzero"),
        Index("ix_credit_user_created", "user_id", "created_at"),
        Index("ix_credit_expires", "expires_at"),
    )


class ReferralCode(Base):
    """Permanent referral code per user."""
    __tablename__ = "referral_codes"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Referral(Base):
    """Referral relationship and earnings."""
    __tablename__ = "referrals"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    referrer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    referred_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    __table_args__ = (
        UniqueConstraint("referrer_id", "referred_id", name="uq_referrer_referred"),
    )


class PromoCode(Base):
    """Promotional codes for earning credits."""
    __tablename__ = "promo_codes"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    code_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_uses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_per_user: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    language: Mapped[str | None] = mapped_column(String(2), nullable=True)
    
    campaign_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    created_by: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PromoCodeRedemption(Base):
    """Track which users have redeemed which promo codes."""
    __tablename__ = "promo_code_redemptions"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    promo_code_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("promo_codes.id"), nullable=False, index=True
    )
    
    credit_ledger_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("credit_ledger.id"), nullable=False
    )
    
    redeemed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    __table_args__ = (
        UniqueConstraint("user_id", "promo_code_id", name="uq_user_promo"),
    )


class CreditExpenseCap(Base):
    """Rate limiting and caps for anti-fraud."""
    __tablename__ = "credit_expense_caps"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    
    monthly_learning_cap: Mapped[int] = mapped_column(Integer, default=1500, nullable=False)
    monthly_learning_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    monthly_referral_cap: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    monthly_referral_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    cap_reset_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    last_activation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
