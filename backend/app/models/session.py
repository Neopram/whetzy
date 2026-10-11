"""Study sessions and individual question responses (the raw event log
that all adaptive models — BKT, Elo, FSRS — are recalibrated from)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base


class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    questions_answered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_combo: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mode: Mapped[str] = mapped_column(String(20), default="study", nullable=False)

    # Alcance con el que se abrió la sesión. La siguiente pregunta se elige
    # dentro de él; sin guardarlo aquí, la primera respetaba el track y las
    # demás salían de cualquier sitio.
    track_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    skill_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # La pregunta que /quiz/start o el `next_question` de /quiz/answer acaban
    # de servir — la única que /quiz/answer debe aceptar ahora (S.4, 2026-10-04).
    # None cuando no queda ninguna por responder (cupo agotado, sin más en el
    # alcance). Se actualiza a la siguiente tras cada respuesta, así que un
    # `question_id` ya respondido deja de coincidir sin una columna aparte
    # para "una vez": sirve para las dos partes del mismo hueco.
    current_question_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    responses: Mapped[list[Response]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="Response.created_at"
    )

    @property
    def is_active(self) -> bool:
        return self.ended_at is None


class Response(Base):
    __tablename__ = "responses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("study_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)  # FSRS grade 1-4
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Which content_version of the question was active when this response was
    # recorded. Lets analytics distinguish answers to v1 from answers to v2.
    question_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # True when the learner pressed "I don't know" instead of answering. Kept
    # apart from `correct=False` so accuracy can be reported honestly and so
    # the BKT posterior can use the unambiguous likelihood (see bkt.update_unknown).
    declared_unknown: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )

    event_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )

    # Per-response snapshots for calibration audit (32.0).
    p_known_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    p_known_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    elo_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    elo_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_p: Mapped[float | None] = mapped_column(Float, nullable=True)

    session: Mapped[StudySession] = relationship(back_populates="responses")
