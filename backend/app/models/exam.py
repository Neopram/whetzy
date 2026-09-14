"""Timed certification mock exam (task 10.3)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db import Base


class MockExamAttempt(Base):
    """One sitting of a certification mock exam.

    The attempt is persisted rather than held client-side for a reason the
    product cares about: the deadline has to be the server's. If the questions
    and the clock lived only in the browser, "timed" would mean "timed unless
    you reload", and a mock whose time limit is optional teaches the wrong thing
    about the real exam - which is the one property a mock exists to rehearse.

    `question_ids` freezes the selection at start so a reload resumes the same
    exam instead of drawing a fresh, easier one.
    """

    __tablename__ = "mock_exam_attempts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    track_id: Mapped[str] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Ordered list of question ids, frozen when the attempt starts.
    question_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # The graded report, stored so a finished attempt can be reread without
    # rescoring (and so the numbers a learner was shown never change later).
    report: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)

    # "in_progress" | "submitted" | "expired"
    status: Mapped[str] = mapped_column(
        String(20), default="in_progress", nullable=False, index=True
    )
