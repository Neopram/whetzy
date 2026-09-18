"""Content versioning: track which version of a question was answered.

Adds content_version to questions (default 1) and question_version to
responses (default 1, stamps the question's content_version at answer time).
Editing a question bumps content_version so old responses remain accurate.

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-09-08 08:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "h8i9j0k1l2m3"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("content_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "responses",
        sa.Column("question_version", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("responses", "question_version")
    op.drop_column("questions", "content_version")
