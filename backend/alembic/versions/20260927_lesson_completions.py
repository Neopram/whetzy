"""Lecciones vistas alguna vez, para exigirlas antes del quiz (32.4).

Tabla nueva, aditiva, sin tocar `lesson_views` (que es solo el contador del
cupo Free y no sirve para esto -- ver el docstring del modelo). Se escribe
siempre que haya sesión, sin mirar el cupo ni el tier del usuario.

Revision ID: 20260927_lesson_completions
Revises: 20260927_lesson_views
"""
import sqlalchemy as sa

from alembic import op

revision = '20260927_lesson_completions'
down_revision = '20260927_lesson_views'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'lesson_completions',
        sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', sa.String(length=64), nullable=False),
        sa.Column('viewed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'skill_id'),
    )


def downgrade() -> None:
    op.drop_table('lesson_completions')
