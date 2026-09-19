"""Add campaign tracking tables (Serie 26 — Distribución Masiva ES).

Revision ID: t9u0v1w2x3y4
Revises: s8t9u0v1w2x3
Create Date: 2026-09-19 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 't9u0v1w2x3y4'
down_revision = 's8t9u0v1w2x3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create campaigns table
    op.create_table(
        'campaigns',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('channel', sa.Enum('youtube', 'devto', 'linkedin', 'email', 'reddit', 'twitter', 'organic', name='campaignchannel'), nullable=False),
        sa.Column('status', sa.Enum('draft', 'active', 'paused', 'archived', name='campaignstatus'), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('url', sa.String(length=2048), nullable=True),
        sa.Column('series', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('launched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_campaign_code'),
    )
    op.create_index('ix_campaigns_code', 'campaigns', ['code'], unique=False)
    op.create_index('ix_campaigns_channel', 'campaigns', ['channel'], unique=False)
    op.create_index('ix_campaigns_status', 'campaigns', ['status'], unique=False)
    op.create_index('ix_campaigns_created_at', 'campaigns', ['created_at'], unique=False)

    # Create campaign_clicks table
    op.create_table(
        'campaign_clicks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('campaign_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('source', sa.String(length=64), nullable=False),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('referrer', sa.String(length=2048), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_campaign_clicks_campaign_id', 'campaign_clicks', ['campaign_id'], unique=False)
    op.create_index('ix_campaign_clicks_user_id', 'campaign_clicks', ['user_id'], unique=False)
    op.create_index('ix_campaign_clicks_created_at', 'campaign_clicks', ['created_at'], unique=False)
    op.create_index('ix_campaign_clicks_source', 'campaign_clicks', ['source'], unique=False)


def downgrade() -> None:
    op.drop_table('campaign_clicks')
    op.drop_table('campaigns')
