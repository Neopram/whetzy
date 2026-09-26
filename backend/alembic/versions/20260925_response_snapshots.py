"""Add per-response calibration snapshots to responses (32.0).

Additive: five nullable float columns. Existing rows get NULL — they
predate the snapshot feature. New responses store before/after values
for p_known and Elo, plus expected_p from the Elo model.

Revision ID: 20260925_response_snap
Revises: 20260925_age_gate
"""
import sqlalchemy as sa

from alembic import op

revision = '20260925_response_snap'
down_revision = '20260925_age_gate'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('responses', sa.Column('p_known_before', sa.Float(), nullable=True))
    op.add_column('responses', sa.Column('p_known_after', sa.Float(), nullable=True))
    op.add_column('responses', sa.Column('elo_before', sa.Float(), nullable=True))
    op.add_column('responses', sa.Column('elo_after', sa.Float(), nullable=True))
    op.add_column('responses', sa.Column('expected_p', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('responses', 'expected_p')
    op.drop_column('responses', 'elo_after')
    op.drop_column('responses', 'elo_before')
    op.drop_column('responses', 'p_known_after')
    op.drop_column('responses', 'p_known_before')
