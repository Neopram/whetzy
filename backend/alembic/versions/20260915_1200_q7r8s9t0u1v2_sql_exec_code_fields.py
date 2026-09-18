"""Add code_es/code_en to questions for sql_exec type.

Stores the full SQL script (CREATE TABLE + INSERT + SELECT with ___) as a
separate field rather than embedding it in question prose. fill_blank_exec
and fix_bug continue to embed code inside question_es/question_en fenced
blocks; sql_exec uses these dedicated columns.

Revision ID: q7r8s9t0u1v2
Revises: p6q7r8s9t0u1
Create Date: 2026-09-15 12:00

"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = 'q7r8s9t0u1v2'
down_revision = 'p6q7r8s9t0u1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text(
        "ALTER TABLE questions ADD COLUMN IF NOT EXISTS code_es TEXT"
    ))
    op.execute(sa.text(
        "ALTER TABLE questions ADD COLUMN IF NOT EXISTS code_en TEXT"
    ))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE questions DROP COLUMN IF EXISTS code_es"))
    op.execute(sa.text("ALTER TABLE questions DROP COLUMN IF EXISTS code_en"))
