"""Add credited_at column to referrals table (29.3).

Revision ID: 20260926_ref_credit
Revises: 20260925_response_snap
Create Date: 2026-09-26

The referral state machine is pending→activated→credited.
credited_at records when the referrer actually received credits
(after the 7-day delay from activation).
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '20260926_ref_credit'
down_revision = '20260925_response_snap'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'referrals',
        sa.Column('credited_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('referrals', 'credited_at')
