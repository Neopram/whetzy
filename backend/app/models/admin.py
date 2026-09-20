"""Admin panel models: audit log, login tracking, sessions, promo codes, credit ledger, GDPR requests, referrals."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db import Base

# `CreditLedger`, `Referral` y `PromoCode` vivian aqui con un esquema propio y
# el mismo `__tablename__` que los de `models/economy.py`, lo que rompia el
# arranque de SQLAlchemy. El que manda es el de economy (lotes FIFO, clave de
# idempotencia, caducidad); aqui solo quedan las tablas que son de admin.



class GDPRRequest(Base):
    __tablename__ = "gdpr_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    request_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    export_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

