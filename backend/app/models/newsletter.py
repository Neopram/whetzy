"""Newsletter subscriber (doble opt-in vía Resend, ledger 26.10 / H.30).

Nadie se suscribe de verdad hasta confirmar: `POST /newsletter/subscribe` crea
la fila con `confirmed=False` y manda un correo con un enlace de un solo uso;
solo `GET /newsletter/confirm` la marca `confirmed=True`. No hay usuario
asociado — cualquiera puede suscribirse sin cuenta en Whetzy — así que el
token vive aquí, no en `password_reset_tokens` ni en `email_verification_tokens`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db import Base


class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(2), nullable=False, default="es")
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # SHA-256 hex del token en claro — el token en claro solo viaja en el correo.
    # Se conserva tras confirmar para que el mismo enlace sirva de baja (RFC 8058).
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
