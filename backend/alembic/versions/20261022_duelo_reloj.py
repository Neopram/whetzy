"""duels.opponent_started_at: el reloj del servidor para el desempate (42.4, H.52).

Las cinco preguntas se entregan de golpe, así que el `response_time_ms` que manda
el cliente no vale para desempatar: se puede declarar 0. El reloj del servidor
empieza al entregarlas, con `created_at` para el retador y con este campo, el
primer /join, para el rival. Los duelos anteriores no tienen marca (NULL): para
el rival se usa entonces su primera respuesta, que es lo único que hay.

Revision ID: 20261022_duelo_reloj
Revises: 20261022_evidence_por_fuente
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261022_duelo_reloj"
down_revision = "20261022_evidence_por_fuente"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("duels", sa.Column("opponent_started_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("duels", "opponent_started_at")
