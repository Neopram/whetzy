"""tracks.is_active: retirar un track sin borrarlo (S.12).

``content_loader`` borraba en el arranque cada track que ya no estaba en
``tracks.json``, y el borrado iba en cascada (``ondelete="CASCADE"``) hasta
módulos, skills y preguntas, y de ahí hasta ``responses``, los intentos de
examen y los certificados de los alumnos. Desde esta migración el cargador lo
retira con ``is_active = false`` y el catálogo, el panel y la selección de
preguntas lo filtran; el historial se queda.

``server_default`` true: todos los tracks que existen hoy están declarados
(el último arranque registró ``pruned_tracks 0``), así que ninguno cambia de
estado al aplicarla.

Revision ID: 20261004_tracks_is_active
Revises: 20261002_newsletter_subscribers
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261004_tracks_is_active"
down_revision = "20261002_newsletter_subscribers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tracks",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("tracks", "is_active")
