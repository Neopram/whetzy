"""Background job model for async task processing.

Series 22.6: Asynchronous work (email, exports, DKT training) via job queue.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, BigInteger, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Job(Base):
    """Background job for async processing: email, exports, model training, etc."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
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
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Job-specific output: {''file_url'': ''s3://...'', ''record_count'': 1000, ...}
    result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Error message if job failed
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        default=func.now(),
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)

    def __repr__(self) -> str:
        return f"<Job id={self.id} user={self.user_id} type={self.job_type} status={self.status}>"
