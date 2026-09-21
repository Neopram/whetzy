"""Reset alembic_version to last valid revision."""
from alembic import op
from sqlalchemy.sql import text

revision = '20260922_0200'
down_revision = '20260922_0150'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DELETE FROM alembic_version"))
    conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('b1c2d3e4f5a6')"))
    conn.commit()

def downgrade() -> None:
    pass
