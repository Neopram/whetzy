"""Add is_admin column and create admin user."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision = '20260922_0150'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('role', sa.String(50), nullable=False, server_default='user'))
    
    conn = op.get_bind()
    conn.execute(text("""
        INSERT INTO users (id, email, username, hashed_password, display_name, avatar_emoji, level, total_xp, current_streak, max_streak, streak_freeze_available, is_premium, is_active, email_verified, language, jwt_version, push_streak_enabled, is_admin, role, created_at)
        VALUES (gen_random_uuid(), 'admin@whetzy.com', 'admin', '$2b$12$a7zErNi.HHmnhMMgKVUniOlaT4Fq/xCcK9Cqr4BQyVtNeMLYDM3ya', 'Admin', 'owl', 1, 0, 0, 0, 1, true, true, true, 'es', 1, true, true, 'admin', now())
        ON CONFLICT (email) DO NOTHING
    """))
    conn.commit()

def downgrade() -> None:
    op.drop_column('users', 'role')
    op.drop_column('users', 'is_admin')
