"""Guardar el alcance (track/skill) de una sesión de estudio.

Sin esto la primera pregunta respetaba el track elegido y todas las demás
salían de cualquier sitio: «Practicar» en Algoritmos servía Ciberseguridad a
la segunda. Dos columnas nullable; las sesiones antiguas quedan sin alcance,
que es lo que eran.

Revision ID: b1c2d3e4f5a6
Revises: a9b0c1d2e3f4
Create Date: 2026-09-19 18:00
"""

import sqlalchemy as sa

from alembic import op

revision = 'b1c2d3e4f5a6'
down_revision = 'a9b0c1d2e3f4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('study_sessions', sa.Column('track_id', sa.String(64), nullable=True))
    op.add_column('study_sessions', sa.Column('skill_id', sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column('study_sessions', 'skill_id')
    op.drop_column('study_sessions', 'track_id')
