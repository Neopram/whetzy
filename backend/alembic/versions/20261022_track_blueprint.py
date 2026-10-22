"""tracks: código del examen, guía, URL de la guía y huella del blueprint (42.12).

Los datos ya están en `content/curriculum/tracks.json` (bloque `certification`)
y no se tocan: `content_loader` corre en cada arranque y rellena estas columnas
desde ahí, igual que hace con `exam_question_count` y compañía. Por eso la
migración solo crea las columnas, nulas, y no copia nada: hasta el primer
arranque con el loader nuevo quedan en NULL, que es «sin blueprint registrado».

Revision ID: 20261022_track_blueprint
Revises: 20261022_duelo_reloj
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261022_track_blueprint"
down_revision = "20261022_duelo_reloj"
branch_labels = None
depends_on = None

_COLUMNS = (
    ("cert_code", 32),
    ("exam_guide", 300),
    ("exam_guide_url", 500),
    ("blueprint_version", 16),
)


def upgrade() -> None:
    for name, length in _COLUMNS:
        op.add_column("tracks", sa.Column(name, sa.String(length), nullable=True))


def downgrade() -> None:
    for name, _length in reversed(_COLUMNS):
        op.drop_column("tracks", name)
