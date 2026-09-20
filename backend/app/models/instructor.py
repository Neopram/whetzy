"""Instructor marketplace models: profiles, courses, enrollments, payouts."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base


class Instructor(Base):
    """Instructor profile; 1:1 with User."""

    __tablename__ = "instructors"
    __table_args__ = (UniqueConstraint("user_id", name="uq_instructor_user"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Verification by admin (28.X feature, depends on 22.1 Admin review)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Payout method: "stripe" | "paddle" | "bank_transfer" (set by H.29)
    payout_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # Payout address: Stripe account ID, Paddle vendor ID, or IBAN
    payout_address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    courses: Mapped[list[InstructorCourse]] = relationship(
        back_populates="instructor", cascade="all, delete-orphan"
    )
    payouts: Mapped[list[InstructorPayout]] = relationship(
        back_populates="instructor", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Instructor {self.display_name!r} user_id={self.user_id}>"


class InstructorCourse(Base):
    """Course published by instructor; 1:N with Instructor."""

    __tablename__ = "instructor_courses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    instructor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("instructors.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Price in cents (USD cents; e.g., 9999 = $99.99)
    price_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Video/materials URLs
    video_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    materials_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Aggregated stats
    enrolled_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_cents: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Status: "draft" | "published" | "archived"
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    instructor: Mapped[Instructor] = relationship(back_populates="courses")
    enrollments: Mapped[list[InstructorEnrollment]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<InstructorCourse {self.title!r} price=${self.price_cents / 100:.2f}>"


class InstructorEnrollment(Base):
    """Student enrollment in instructor course; N:N (user:course)."""

    __tablename__ = "instructor_enrollments"
    __table_args__ = (
        UniqueConstraint("course_id", "user_id", name="uq_instructor_course_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("instructor_courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Progress: 0-100
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Completion timestamp (null if not completed)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    course: Mapped[InstructorCourse] = relationship(back_populates="enrollments")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<InstructorEnrollment course_id={self.course_id} user_id={self.user_id} progress={self.progress_percent}%>"


class InstructorPayout(Base):
    """Monthly/quarterly payout record per instructor."""

    __tablename__ = "instructor_payouts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    instructor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("instructors.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Period: YYYY-MM start and end dates
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Total earnings in cents for this period (after platform split)
    earnings_cents: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Status: "pending" | "processing" | "completed" | "failed"
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)

    # Actual payout date (null if not yet processed)
    payout_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    instructor: Mapped[Instructor] = relationship(back_populates="payouts")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<InstructorPayout instructor_id={self.instructor_id} period={self.period_start.strftime('%Y-%m')} status={self.status}>"
