"""paddle_events: deduplicación y orden de los webhooks de Paddle (D-10).

Paddle entrega cada evento al menos una vez y sin orden garantizado. Hasta
ahora el receptor solo registraba `event_id` en el log: un reintento volvía a
aplicar el evento, y un `subscription.updated` (active) que llegaba después
del `subscription.canceled` de la misma suscripción devolvía el plan. La
tabla guarda cada evento aplicado; ver `app/models/paddle_event.py`.

Solo crea una tabla nueva, vacía: no toca filas existentes y la versión
anterior del código la ignora, así que es segura con despliegues solapados.

ID corto (22 caracteres): `alembic_version` es `varchar(32)` (#165).

Revision ID: 20261012_paddle_events
Revises: 20261010_tutor_tokens
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261012_paddle_events"
down_revision = "20261010_tutor_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "paddle_events",
        sa.Column("event_id", sa.String(length=64), primary_key=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_paddle_events_entity_id", "paddle_events", ["entity_id"])


def downgrade() -> None:
    op.drop_index("ix_paddle_events_entity_id", table_name="paddle_events")
    op.drop_table("paddle_events")
