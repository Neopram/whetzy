"""Create admin user in production."""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, UTC
import uuid

revision = "final_create_admin"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Hash password: Admin@123456
    pwd_hash = "$2b$12$a7zErNi.HHmnhMMgKVUniOlaT4Fq/xCcK9Cqr4BQyVtNeMLYDM3ya"
    
    conn.execute(
        sa.text("""
            INSERT INTO users (id, email, username, hashed_password, display_name, avatar_emoji,
            level, total_xp, current_streak, max_streak, streak_freeze_available,
            is_premium, is_active, email_verified, language, jwt_version,
            push_streak_enabled, created_at)
            VALUES (:id, :email, :username, :pwd, :display_name, :avatar_emoji,
            :level, :total_xp, :current_streak, :max_streak, :streak_freeze_available,
            :is_premium, :is_active, :email_verified, :language, :jwt_version,
            :push_streak_enabled, :created_at)
            ON CONFLICT (email) DO UPDATE SET hashed_password = EXCLUDED.hashed_password
        """),
        {
            "id": str(uuid.uuid4()),
            "email": "admin@whetzy.com",
            "username": "admin",
            "pwd": pwd_hash,
            "display_name": "Admin",
            "avatar_emoji": "owl",
            "level": 1,
            "total_xp": 0,
            "current_streak": 0,
            "max_streak": 0,
            "streak_freeze_available": 1,
            "is_premium": True,
            "is_active": True,
            "email_verified": True,
            "language": "es",
            "jwt_version": 1,
            "push_streak_enabled": True,
            "created_at": datetime.now(UTC),
        },
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM users WHERE email = 'admin@whetzy.com'"))
