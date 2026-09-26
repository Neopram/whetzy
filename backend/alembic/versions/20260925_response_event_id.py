"""Add event_id to responses for offline queue idempotency (33.2).

Additive: nullable column + unique index. Existing rows keep NULL.

Revision ID: 20260925_event_id
Revises: 20260925_tutor_cert
"""
import sqlalchemy as sa

from alembic import op

revision = '20260925_event_id'
down_revision = '20260925_tutor_cert'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('responses', sa.Column('event_id', sa.String(64), nullable=True))
    op.create_index('ix_responses_event_id', 'responses', ['event_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_responses_event_id', table_name='responses')
    op.drop_column('responses', 'event_id')
