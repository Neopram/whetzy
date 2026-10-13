"""Eventos de Paddle ya procesados (D-10, dueño, 2026-10-12).

Paddle entrega los webhooks *al menos una vez* y sin orden garantizado. Esta
tabla da las dos garantías que faltaban:

- **Deduplicación**: `event_id` es la clave primaria; un evento que ya está
  aquí no se vuelve a aplicar.
- **Orden**: `entity_id` (`sub_…`, `txn_…`, `adj_…`) y `occurred_at` permiten
  descartar un `subscription.*` más viejo que el último aplicado a esa misma
  suscripción, que si no devolvía el plan a quien ya lo había cancelado.

La fila se escribe en la misma transacción que el efecto del evento: si
aplicarlo falla, no queda fila y el reintento de Paddle lo vuelve a intentar.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PaddleEvent(Base):
    __tablename__ = "paddle_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
