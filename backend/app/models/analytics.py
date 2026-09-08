"""Analytics event log (5.4).

One row per user-action event. The `event_type` column carries a stable
string identifier; `properties` holds any extra JSON context.

Fired events (initial set):
  user_registered   — on POST /auth/register
  first_quiz_answer — on the user's very first quiz answer (questions_answered == 1)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    __table_args__ = (
        Index("ix_analytics_user_type", "user_id", "event_type"),
        Index("ix_analytics_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    properties: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
