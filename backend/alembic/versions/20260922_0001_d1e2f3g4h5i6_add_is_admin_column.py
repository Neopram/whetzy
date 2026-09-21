"""Add is_admin column to users table.

Revision ID: d1e2f3g4h5i6
Revises: b1c2d3e4f5a6
Create Date: 2026-09-22 00:01:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "d1e2f3g4h5i6"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add is_admin column."""
    op.add_column("users", sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    """Remove is_admin column."""
    op.drop_column("users", "is_admin")
