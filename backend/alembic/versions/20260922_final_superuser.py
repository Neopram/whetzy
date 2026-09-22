"""Create superuser on fresh DB."""
from alembic import op
from sqlalchemy.sql import text

revision = '20260922_final'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        INSERT INTO users (id, email, username, hashed_password, display_name, avatar_emoji, is_premium, is_active, email_verified, role, created_at)
        VALUES (gen_random_uuid(), 'admin@whetzy.com', 'admin', '$2b$12$a7zErNi.HHmnhMMgKVUniOlaT4Fq/xCcK9Cqr4BQyVtNeMLYDM3ya', 'Admin', '👑', true, true, true, 'superuser', now())
        ON CONFLICT DO NOTHING
    """))
    conn.commit()

def downgrade() -> None:
    pass
