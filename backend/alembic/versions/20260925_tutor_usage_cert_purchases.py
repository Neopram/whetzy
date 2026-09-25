"""Cupo del tutor y compra de certificación (38.6 y 38.7, ADR-49).

Dos tablas nuevas, sin tocar las existentes: `tutor_usage` (explicaciones por
usuario y día UTC) y `certification_purchases` (pago único por usuario y track
de certificación). Aditiva: nada que rellenar.

Revision ID: 20260925_tutor_cert
Revises: 20260925_leagues_opt_out
"""
import sqlalchemy as sa

from alembic import op

revision = '20260925_tutor_cert'
down_revision = '20260925_leagues_opt_out'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'tutor_usage',
        sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('explanations', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('user_id', 'day'),
    )
    op.create_table(
        'certification_purchases',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('track_id', sa.String(length=64), sa.ForeignKey('tracks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('price_usd', sa.Float(), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('external_ref', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'track_id', name='uq_certification_purchases_user_track'),
    )


def downgrade() -> None:
    op.drop_table('certification_purchases')
    op.drop_table('tutor_usage')
