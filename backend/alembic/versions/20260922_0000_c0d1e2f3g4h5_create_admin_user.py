"""Create admin@whetzy.com user if not exists.

Revision ID: c0d1e2f3g4h5
Revises: d1e2f3g4h5i6
Create Date: 2026-09-22 00:00:00.000000

"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from alembic import op
import sqlalchemy as sa

revision = "c0d1e2f3g4h5"
down_revision = "d1e2f3g4h5i6"
branch_labels = None
depends_on = None

ADMIN_PASSWORD_HASH = "$2b$12$a7zErNi.HHmnhMMgKVUniOlaT4Fq/xCcK9Cqr4BQyVtNeMLYDM3ya"

def upgrade() -> None:
    """Create admin user if not exists."""
    conn = op.get_bind()
    
    stmt = sa.text("""
        INSERT INTO users (
            id, email, username, hashed_password, display_name, avatar_emoji,
            level, total_xp, current_streak, max_streak, streak_freeze_available,
            language, email_verified, is_active, is_admin, jwt_version,
            push_streak_enabled, created_at
        )
        VALUES (
            :id, :email, :username, :hashed_password, :display_name, :avatar_emoji,
            :level, :total_xp, :current_streak, :max_streak, :streak_freeze_available,
            :language, :email_verified, :is_active, :is_admin, :jwt_version,
            :push_streak_enabled, :created_at
        )
        ON CONFLICT (email) DO NOTHING
    """)
    
    conn.execute(
        stmt,
        {
            "id": str(uuid.uuid4()),
            "email": "admin@whetzy.com",
            "username": "admin",
            "hashed_password": ADMIN_PASSWORD_HASH,
            "display_name": "Admin",
            "avatar_emoji": "🦉",
            "level": 1,
            "total_xp": 0,
            "current_streak": 0,
            "max_streak": 0,
            "streak_freeze_available": 1,
            "language": "es",
            "email_verified": True,
            "is_active": True,
            "is_admin": True,
            "jwt_version": 1,
            "push_streak_enabled": True,
            "created_at": datetime.now(UTC),
        },
    )


def downgrade() -> None:
    """Remove admin user."""
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM users WHERE email = 'admin@whetzy.com'"))
