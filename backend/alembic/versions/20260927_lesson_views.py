"""Lecciones abiertas por usuario y día para el cupo del plan Free (39.4, ADR-50a).

Una tabla nueva, sin tocar las existentes: `lesson_views` (usuario, skill, día UTC).
Solo se escribe con `FREE_DAILY_QUOTA_ENABLED=true`. Aditiva: nada que rellenar.

Revision ID: 20260927_lesson_views
Revises: 20260926_eu_withdrawal
"""
import sqlalchemy as sa

from alembic import op

revision = '20260927_lesson_views'
down_revision = '20260926_eu_withdrawal'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'lesson_views',
        sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', sa.String(length=64), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'skill_id', 'day'),
    )


def downgrade() -> None:
    op.drop_table('lesson_views')
