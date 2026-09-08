"""User, per-skill learning state, and earned-badge models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_emoji: Mapped[str] = mapped_column(String(16), default="🦉", nullable=False)

    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    streak_freeze_available: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    language: Mapped[str] = mapped_column(String(2), default="es", nullable=False)
    # Incremented on password change/reset to invalidate existing tokens (ASVS V3.3).
    jwt_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Push notification preferences (P.13)
    push_streak_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_streak_reminder_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Stripe subscription (7.2)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    subscription_status: Mapped[str | None] = mapped_column(String(32), nullable=True)  # active|canceled|past_due|trialing
    subscription_tier: Mapped[str | None] = mapped_column(String(16), nullable=True)  # plus|pro
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    skill_states: Mapped[list[UserSkillState]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    badges: Mapped[list[UserBadge]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.username!r}>"


class UserSkillState(Base):
    """Per-user, per-skill mastery/scheduling state combining BKT, Elo and FSRS."""

    __tablename__ = "user_skill_states"
    __table_args__ = (UniqueConstraint("user_id", "skill_id", name="uq_user_skill_state"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )

    p_known: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)
    elo_rating: Mapped[float] = mapped_column(Float, default=1500.0, nullable=False)
    fsrs_stability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fsrs_difficulty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fsrs_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="skill_states")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserSkillState user={self.user_id} skill={self.skill_id} p={self.p_known:.2f}>"


class UserBadge(Base):
    __tablename__ = "user_badges"
    __table_args__ = (UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    badge_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("badges.id", ondelete="CASCADE"), nullable=False, index=True
    )
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="badges")
