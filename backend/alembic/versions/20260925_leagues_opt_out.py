"""Ligas opcionales: el usuario puede salir de la clasificación (35.4).

Una columna booleana con default de servidor `false`: aditiva, sin backfill;
quien ya existe sigue compitiendo como hasta ahora.

Revision ID: 20260925_leagues_opt_out
Revises: 20260924_onboarding_profile
"""
import sqlalchemy as sa

from alembic import op

revision = '20260925_leagues_opt_out'
down_revision = '20260924_onboarding_profile'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('leagues_opt_out', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column('users', 'leagues_opt_out')
