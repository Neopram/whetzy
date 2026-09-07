"""Async 1-v-1 duel model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db import Base


class Duel(Base):
    """An asynchronous 1-v-1 quiz challenge between two users."""

    __tablename__ = "duels"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    challenger_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    opponent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # JSON list of 5 question IDs (strings)
    question_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # JSON list of {question_id, selected_index, response_time_ms, correct}
    challenger_answers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    opponent_answers: Mapped[list | None] = mapped_column(JSON, nullable=True)

    challenger_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    opponent_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    winner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # "pending" | "in_progress" | "completed"
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
