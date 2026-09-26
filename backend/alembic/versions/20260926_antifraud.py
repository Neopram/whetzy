"""Add anti-fraud tables (29.5).

Revision ID: 20260926_antifraud
Revises: 20260926_ref_credit
Create Date: 2026-09-26

Device fingerprints and fraud review queue for referral anti-fraud.
"""

import sqlalchemy as sa

from alembic import op

revision = '20260926_antifraud'
down_revision = '20260926_ref_credit'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'device_fingerprints',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('fingerprint_hash', sa.String(128), nullable=False),
        sa.Column('ip_hash', sa.String(128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_device_fingerprints_user_id', 'device_fingerprints', ['user_id'])
    op.create_index('ix_device_fingerprints_fingerprint_hash', 'device_fingerprints', ['fingerprint_hash'])
    op.create_index('ix_device_fingerprints_ip_hash', 'device_fingerprints', ['ip_hash'])
    op.create_index('ix_device_fp_hash_created', 'device_fingerprints', ['fingerprint_hash', 'created_at'])
    op.create_index('ix_device_ip_hash_created', 'device_fingerprints', ['ip_hash', 'created_at'])

    op.create_table(
        'fraud_review_queue',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('referrer_id', sa.Uuid(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('reason', sa.String(100), nullable=False),
        sa.Column('activation_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fraud_review_queue_referrer_id', 'fraud_review_queue', ['referrer_id'])


def downgrade() -> None:
    op.drop_table('fraud_review_queue')
    op.drop_table('device_fingerprints')
