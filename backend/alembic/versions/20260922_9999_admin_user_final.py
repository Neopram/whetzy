"""Create admin user with full system control."""
from alembic import op
from sqlalchemy.sql import text

revision = '20260922_9999'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        INSERT INTO users (id, email, username, hashed_password, display_name, avatar_emoji, level, total_xp, current_streak, max_streak, streak_freeze_available, is_premium, is_active, email_verified, language, jwt_version, push_streak_enabled, role, created_at)
        VALUES (gen_random_uuid(), 'admin@whetzy.com', 'admin', '$2b$12$a7zErNi.HHmnhMMgKVUniOlaT4Fq/xCcK9Cqr4BQyVtNeMLYDM3ya', 'Admin', 'owl', 1, 0, 0, 0, 1, true, true, true, 'es', 1, true, 'admin', now())
        ON CONFLICT (email) DO NOTHING
    """))
    conn.commit()

def downgrade() -> None:
    pass
