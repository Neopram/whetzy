"""Admin panel models: GDPR requests and the admin action log (44.1)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
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


class AdminActionLog(Base):
    """Registro de administración (44.1, `docs/PLAN_BACKOFFICE.md` B6).

    Una fila por cada vez que el dueño abre la ficha de alguien (`view`) o actúa
    sobre su cuenta (44.2). Solo se añade: ninguna ruta lo edita ni lo borra. Si
    se borra el actor o el afectado, la fila queda con el id a NULL y su rastro.
    """

    __tablename__ = "admin_action_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # Obligatorio en las acciones (44.2); `view` no lo lleva.
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[dict[str, Any] | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
