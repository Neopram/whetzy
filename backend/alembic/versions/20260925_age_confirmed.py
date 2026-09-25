"""Add age_confirmed to users for age gate (19.11).

Additive: non-nullable boolean defaulting to false. Existing users
get false — they registered before the gate existed.

Revision ID: 20260925_age_gate
Revises: 20260925_event_id
"""
import sqlalchemy as sa

from alembic import op

revision = '20260925_age_gate'
down_revision = '20260925_event_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('age_confirmed', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'age_confirmed')
