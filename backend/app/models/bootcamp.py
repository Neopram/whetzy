"""Bootcamp models: structured learning paths with schedule and daily goals (19.4)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base


class Bootcamp(Base):
    __tablename__ = "bootcamps"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name_es: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    description_es: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description_en: Mapped[str] = mapped_column(Text, nullable=False, default="")
    duration_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    daily_goal_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    icon: Mapped[str] = mapped_column(String(32), nullable=False, default="rocket")
    color: Mapped[str] = mapped_column(String(16), nullable=False, default="#6366f1")
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    weeks: Mapped[list[BootcampWeek]] = relationship(
        back_populates="bootcamp", cascade="all, delete-orphan",
        order_by="BootcampWeek.week_number",
    )
    enrollments: Mapped[list[BootcampEnrollment]] = relationship(
        back_populates="bootcamp", cascade="all, delete-orphan",
    )


class BootcampWeek(Base):
    __tablename__ = "bootcamp_weeks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    bootcamp_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bootcamps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    track_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title_es: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    title_en: Mapped[str] = mapped_column(String(200), nullable=False, default="")

    bootcamp: Mapped[Bootcamp] = relationship(back_populates="weeks")


class BootcampEnrollment(Base):
    __tablename__ = "bootcamp_enrollments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    bootcamp_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bootcamps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    current_week: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    bootcamp: Mapped[Bootcamp] = relationship(back_populates="enrollments")
