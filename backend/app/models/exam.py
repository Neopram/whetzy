"""Timed exams: certification mock (10.3), track final and test-out (17.2)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
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

    # "certification" (10.3) | "track_final" | "test_out" (17.2). The three
    # share this table because they are the same object — a frozen draw with a
    # server-side deadline — and differ only in how they are blueprinted and
    # what passing earns.
    kind: Mapped[str] = mapped_column(
        String(20), default="certification", server_default="certification", nullable=False,
        index=True,
    )
    # Set only for a test-out, which is scoped to one module.
    module_id: Mapped[str | None] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # Frozen at start on purpose: a pass mark that a later config change can
    # move retroactively would turn yesterday's certificates into maybes.
    # Null for the certification mock, which deliberately reports a raw
    # percentage and refuses to declare a pass against an invented scale.
    pass_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

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


class Certificate(Base):
    """Proof that a learner passed a track's final exam (17.2).

    The row is the certificate. It is minted once per (user, track): re-sitting
    a track you already passed returns the same code rather than minting a
    second one, so a URL someone put on their CV never goes dead and there is
    never a question of which of two certificates is "the" one.

    `score_pct` and `questions` are copied in rather than read back through
    `attempt_id` at display time. The attempt is the audit trail; the
    certificate is a statement made on a date, and a statement that silently
    changes when the exam blueprint changes is not proof of anything.
    """

    __tablename__ = "certificates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Public, unguessable handle. The verification page is unauthenticated, so
    # this is the only thing that keeps certificates from being enumerable.
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    track_id: Mapped[str] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mock_exam_attempts.id", ondelete="CASCADE"), nullable=False
    )

    score_pct: Mapped[float] = mapped_column(Float, nullable=False)
    questions: Mapped[int] = mapped_column(Integer, nullable=False)

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # A certificate is withdrawn, never deleted: a URL that 404s cannot be told
    # apart from one that was never issued, and "we revoked it" is information
    # the person checking deserves.
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)


class CertificationPurchase(Base):
    """Derecho a presentarse al examen certificador de un track (38.7, ADR-49).

    Pago único: una fila por (usuario, track) y los reintentos no vuelven a pasar
    por caja. `price_usd` guarda lo que se pagó ese día; si el precio cambia, lo
    comprado no cambia con él.
    """

    __tablename__ = "certification_purchases"
    __table_args__ = (
        UniqueConstraint("user_id", "track_id", name="uq_certification_purchases_user_track"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    track_id: Mapped[str] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False
    )
    price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    # "grant" (regalo del dueño o del admin) | el proveedor de pago cuando abra H.19
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
