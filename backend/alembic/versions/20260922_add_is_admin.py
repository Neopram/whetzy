"""Add is_admin column to users table."""
from alembic import op
import sqlalchemy as sa

revision = '20260922_add_is_admin'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_admin column if it doesn't exist
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'is_admin')
