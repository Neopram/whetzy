"""Add lessons table.

Stores short instructional content (150-300 words ES/EN + worked example)
tied to one skill. Delivered before adaptive quiz — instruction-before-practice
(Sweller worked-example effect). Multiple lessons per skill via `order` column.

Revision ID: p6q7r8s9t0u1
Revises: o5p6q7r8s9t0
Create Date: 2026-09-15 10:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "p6q7r8s9t0u1"
down_revision = "o5p6q7r8s9t0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idempotent DDL: prod already has this table from when F20 was deployed
    # via SQLAlchemy create_all before this migration file was committed.
    # Using IF NOT EXISTS prevents DuplicateTableError on re-deploy.
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS lessons (
            id          VARCHAR(64) PRIMARY KEY,
            skill_id    VARCHAR(64) NOT NULL
                            REFERENCES skills(id) ON DELETE CASCADE,
            title_es    VARCHAR(200) NOT NULL,
            title_en    VARCHAR(200) NOT NULL,
            body_es     TEXT NOT NULL,
            body_en     TEXT NOT NULL,
            example_code  TEXT,
            example_output TEXT,
            source      TEXT NOT NULL,
            "order"     INTEGER NOT NULL DEFAULT 1
        )
    """))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_lessons_skill_id ON lessons (skill_id)"
    ))


def downgrade() -> None:
    op.drop_index("ix_lessons_skill_id", "lessons")
    op.drop_table("lessons")
