"""Leagues, badges, and daily missions."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class League(Base):
    """A weekly competitive cohort tier, Duolingo-style (bronze..diamond)."""

    __tablename__ = "leagues"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    min_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    entries: Mapped[list[LeagueEntry]] = relationship(
        back_populates="league", cascade="all, delete-orphan"
    )


class LeagueEntry(Base):
    """A user's standing within a league for a given ISO week."""

    __tablename__ = "league_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "league_id", "week_start", name="uq_league_entry"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    league_id: Mapped[str] = mapped_column(
        ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)

    league: Mapped[League] = relationship(back_populates="entries")


class Badge(Base):
    """A collectible achievement definition."""

    __tablename__ = "badges"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name_es: Mapped[str] = mapped_column(String(150), nullable=False)
    name_en: Mapped[str] = mapped_column(String(150), nullable=False)
    icon: Mapped[str] = mapped_column(String(16), default="🏅", nullable=False)
    description_es: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    description_en: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    criteria_type: Mapped[str] = mapped_column(String(50), nullable=False)
    criteria_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Mission(Base):
    """A daily-mission template (target + reward)."""

    __tablename__ = "missions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_value: Mapped[int] = mapped_column(Integer, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    name_es: Mapped[str] = mapped_column(String(150), nullable=False)
    name_en: Mapped[str] = mapped_column(String(150), nullable=False)


class UserMission(Base):
    """A user's daily progress against a Mission template."""

    __tablename__ = "user_missions"
    __table_args__ = (
        UniqueConstraint("user_id", "mission_id", "date", name="uq_user_mission_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mission_id: Mapped[str] = mapped_column(
        ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
