"""Add level column to modules (17.4 — cursos por niveles).

Each module gets an integer level (1=Fundamentos, 2=Intermedio, 3=Avanzado)
that groups modules within a track into three courses. The default of 1 lets
existing rows stay functional until the content loader re-seeds them.

Revision ID: s9t0u1v2w3x4
Revises: r8s9t0u1v2w3
Create Date: 2026-09-16 09:00
"""

import sqlalchemy as sa

from alembic import op

revision = 's9t0u1v2w3x4'
down_revision = 'r8s9t0u1v2w3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'modules',
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
    )


def downgrade() -> None:
    op.drop_column('modules', 'level')
