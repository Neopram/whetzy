"""User-submitted reports flagging defective or incorrect questions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.user import User

# `ai_explanation`: la explicación del tutor IA estaba mal (transparencia de IA,
# AI Act art. 50); la nota lleva el texto que vio el alumno, que no se guarda en
# otro sitio porque se genera al vuelo.
VALID_REASONS = frozenset({"wrong_answer", "typo", "outdated", "confusing", "other", "ai_explanation"})
REPORT_NOTES_MAX = 4000


class QuestionReport(Base):
    __tablename__ = "question_reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship("User")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<QuestionReport {self.id} q={self.question_id} reason={self.reason}>"
