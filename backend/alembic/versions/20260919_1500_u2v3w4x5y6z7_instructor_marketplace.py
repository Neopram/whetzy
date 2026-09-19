"""Add instructor marketplace tables (Serie 28 - Marketplace + Payouts).

Revision ID: u2v3w4x5y6z7
Revises: t9u0v1w2x3y4
Create Date: 2026-09-19 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'u2v3w4x5y6z7'
down_revision = 't9u0v1w2x3y4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create instructors table (1:1 with users)
    op.create_table(
        'instructors',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(length=512), nullable=True),
        sa.Column('website', sa.String(length=512), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payout_method', sa.String(length=32), nullable=True),
        sa.Column('payout_address', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_instructor_user'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_instructors_user_id', 'instructors', ['user_id'], unique=False)
    op.create_index('ix_instructors_verified_at', 'instructors', ['verified_at'], unique=False)

    # Create instructor_courses table (courses by instructors)
    op.create_table(
        'instructor_courses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('instructor_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price_cents', sa.BigInteger(), nullable=False),
        sa.Column('video_url', sa.String(length=512), nullable=True),
        sa.Column('materials_url', sa.String(length=512), nullable=True),
        sa.Column('enrolled_count', sa.Integer(), default=0, nullable=False),
        sa.Column('revenue_cents', sa.BigInteger(), default=0, nullable=False),
        sa.Column('status', sa.String(length=32), default='draft', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['instructor_id'], ['instructors.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_instructor_courses_instructor_id', 'instructor_courses', ['instructor_id'], unique=False)
    op.create_index('ix_instructor_courses_status', 'instructor_courses', ['status'], unique=False)
    op.create_index('ix_instructor_courses_created_at', 'instructor_courses', ['created_at'], unique=False)

    # Create instructor_enrollments table (student enrollments in courses)
    op.create_table(
        'instructor_enrollments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('course_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('progress_percent', sa.Integer(), default=0, nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'user_id', name='uq_instructor_course_user'),
        sa.ForeignKeyConstraint(['course_id'], ['instructor_courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_instructor_enrollments_course_id', 'instructor_enrollments', ['course_id'], unique=False)
    op.create_index('ix_instructor_enrollments_user_id', 'instructor_enrollments', ['user_id'], unique=False)
    op.create_index('ix_instructor_enrollments_enrolled_at', 'instructor_enrollments', ['enrolled_at'], unique=False)

    # Create instructor_payouts table (monthly payouts)
    op.create_table(
        'instructor_payouts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('instructor_id', sa.UUID(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('earnings_cents', sa.BigInteger(), default=0, nullable=False),
        sa.Column('status', sa.String(length=32), default='pending', nullable=False),
        sa.Column('payout_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['instructor_id'], ['instructors.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_instructor_payouts_instructor_id', 'instructor_payouts', ['instructor_id'], unique=False)
    op.create_index('ix_instructor_payouts_status', 'instructor_payouts', ['status'], unique=False)
    op.create_index('ix_instructor_payouts_period_start', 'instructor_payouts', ['period_start'], unique=False)
    op.create_index('ix_instructor_payouts_created_at', 'instructor_payouts', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('instructor_payouts')
    op.drop_table('instructor_enrollments')
    op.drop_table('instructor_courses')
    op.drop_table('instructors')
