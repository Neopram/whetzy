"""Respuestas de segmento del onboarding en el usuario (34.11).

El onboarding de 24.3 preguntaba experiencia, objetivo y horas por semana y
no guardaba nada. Tres SmallInteger nullables (índice de la opción, 0-2):
aditiva, sin backfill.

Revision ID: 20260924_onboarding_profile
Revises: 20260924_owner_role
"""
import sqlalchemy as sa

from alembic import op

revision = '20260924_onboarding_profile'
down_revision = '20260924_owner_role'
branch_labels = None
depends_on = None

_COLS = ('onboarding_experience', 'onboarding_goal', 'onboarding_weekly_time')


def upgrade() -> None:
    for c in _COLS:
        op.add_column('users', sa.Column(c, sa.SmallInteger(), nullable=True))


def downgrade() -> None:
    for c in reversed(_COLS):
        op.drop_column('users', c)
