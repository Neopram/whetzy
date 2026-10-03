"""Newsletter subscriber (doble opt-in vía Resend, ledger 26.10 / H.30).

Nadie se suscribe de verdad hasta confirmar: `POST /newsletter/subscribe` crea
la fila con `confirmed=False` y manda un correo con un enlace de un solo uso;
solo confirmar (vía `POST /newsletter/confirm`, tras el botón de la página de
`GET`) la marca `confirmed=True`. No hay usuario asociado — cualquiera puede
suscribirse sin cuenta en Whetzy.

El enlace del correo no guarda ningún secreto en esta tabla: es un JWT firmado
con `create_unsubscribe_token(id)` (`app/core/security.py`), el mismo mecanismo
que ya usa `email_prefs.py` para el marketing de cuentas con sesión. Stateless
a propósito — revisión de `[S5]` en el PR #94: un hash guardado no se puede
reconstruir para el enlace de baja de un envío futuro (todavía no existe el
envío periódico, pero el token sí tiene que sobrevivirlo), y expiraba nunca.
Firmado, se puede volver a generar el mismo token para la misma fila siempre
que haga falta, y expira a los 400 días como cualquier enlace de baja.
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
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Último envío de confirmación — cierra la ventana de abuso que señaló [S5]:
    # sin esto, repetir POST /subscribe sobre un email ajeno manda un correo por
    # petición, sin límite propio del endpoint.
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
