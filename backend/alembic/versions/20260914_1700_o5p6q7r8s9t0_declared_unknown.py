"""Explicit "I don't know" as a first-class observation.

Until now the only outcomes were right and wrong, so a lucky guess on a
four-option question entered BKT as evidence of knowledge and an honest
admission of ignorance was indistinguishable from a mistake. Both columns
here exist to keep those three states apart:

  responses.declared_unknown   — this answer was an admission, not an attempt
  user_skill_states.unknown_count — so accuracy never counts honesty as failure

Additive only, with server defaults, so existing rows keep their meaning:
everything answered before this migration was a real attempt.

Revision ID: o5p6q7r8s9t0
Revises: n4o5p6q7r8s9
Create Date: 2026-09-14 17:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "o5p6q7r8s9t0"
down_revision = "n4o5p6q7r8s9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "responses",
        sa.Column(
            "declared_unknown",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "user_skill_states",
        sa.Column(
            "unknown_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("user_skill_states", "unknown_count")
    op.drop_column("responses", "declared_unknown")
