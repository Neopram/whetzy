"""Background job model for async task processing.

Series 22.6: Asynchronous work (email, exports, DKT training) via job queue.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, TIMESTAMP, BigInteger, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# Postgres manda (es lo que crea la migracion x5y6z7a8b9c0), pero la suite de
# tests monta el esquema sobre SQLite desde el metadata y SQLite no compila JSONB.
JSON_COLUMN = JSONB().with_variant(JSON(), "sqlite")


class Job(Base):
    """Background job for async processing: email, exports, model training, etc."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Job type: ''email'', ''export_csv'', ''export_pdf'', ''dkt_train'', etc.
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Status: ''queued'', ''running'', ''done'', ''failed''
    status: Mapped[str] = mapped_column(
        String(20),
        default="queued",
        nullable=False,
    )

    # Job-specific input: {''format'': ''csv'', ''track_id'': 123, ...}
    payload: Mapped[dict] = mapped_column(JSON_COLUMN, nullable=False, default=dict)

    # Job-specific output: {''file_url'': ''s3://...'', ''record_count'': 1000, ...}
    result: Mapped[dict | None] = mapped_column(JSON_COLUMN, nullable=True)

    # Error message if job failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        default=func.now(),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    def __repr__(self) -> str:
        return f"<Job id={self.id} user={self.user_id} type={self.job_type} status={self.status}>"
