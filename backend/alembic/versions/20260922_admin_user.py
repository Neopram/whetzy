"""Create admin superuser."""
from uuid import uuid4
from alembic import op
from sqlalchemy import text

revision = '20260922_admin'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    
    # Check if admin already exists
    result = connection.execute(
        text("SELECT 1 FROM users WHERE email = 'admin@whetzy.com' LIMIT 1")
    )
    if result.fetchone():
        return  # Already exists, skip
    
    # Insert admin user with ALL required NOT NULL fields
    admin_id = str(uuid4())
    try:
        connection.execute(
            text(
                f"INSERT INTO users ("
                f"id, email, username, hashed_password, display_name, avatar_emoji, "
                f"level, total_xp, current_streak, max_streak, streak_freeze_available, "
                f"is_premium, is_active, is_admin, email_verified, language, jwt_version, push_streak_enabled, "
                f"role, created_at"
                f") VALUES ("
                f"'{admin_id}', 'admin@whetzy.com', 'admin', '$2b$12$a7zErNi.HHmnhMMgKVUniOlaT4Fq/xCcK9Cqr4BQyVtNeMLYDM3ya', 'Admin', '👑', "
                f"1, 0, 0, 0, 1, "
                f"true, true, true, true, 'es', 1, true, "
                f"'superuser', now()"
                f")"
            )
        )
        connection.commit()
    except Exception:
        connection.rollback()


def downgrade() -> None:
    pass
