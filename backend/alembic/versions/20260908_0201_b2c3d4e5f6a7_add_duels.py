"""add_duels

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-08 02:01:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "duels",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("challenger_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("opponent_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", sa.String(64), nullable=False),
        sa.Column("question_ids", sa.JSON(), nullable=False),
        sa.Column("challenger_answers", sa.JSON(), nullable=True),
        sa.Column("opponent_answers", sa.JSON(), nullable=True),
        sa.Column("challenger_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opponent_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("winner_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["challenger_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["opponent_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["winner_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_duels_challenger_id", "duels", ["challenger_id"])
    op.create_index("ix_duels_opponent_id", "duels", ["opponent_id"])
    op.create_index("ix_duels_status", "duels", ["status"])


def downgrade() -> None:
    op.drop_index("ix_duels_status", table_name="duels")
    op.drop_index("ix_duels_opponent_id", table_name="duels")
    op.drop_index("ix_duels_challenger_id", table_name="duels")
    op.drop_table("duels")
