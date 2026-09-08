"""Baseline migration — captures schema created by create_all before Alembic was introduced.

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-09-08
"""

from __future__ import annotations

revision = "a1b2c3d4e5f6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Schema already exists in production (created via SQLAlchemy create_all).
    # This migration is intentionally empty — its sole purpose is to serve as
    # the stamped baseline so subsequent migrations can run incrementally.
    pass


def downgrade() -> None:
    pass
