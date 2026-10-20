"""admin_action_log: el registro de administración del back-office (44.1).

Una fila por cada ficha que abre el dueño (`view`) y, desde 44.2, por cada
acción sobre una cuenta, con su motivo. Solo se añade (`docs/PLAN_BACKOFFICE.md`
B6). Los ids de actor y afectado pasan a NULL si se borra el usuario: el rastro
se queda.

Revision ID: 20261020_admin_action_log
Revises: 20261019_question_interactive
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261020_admin_action_log"
down_revision = "20261019_question_interactive"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_action_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("target_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("data", sa.JSON(none_as_null=True), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_action_log_actor_id", "admin_action_log", ["actor_id"])
    op.create_index("ix_admin_action_log_target_user_id", "admin_action_log", ["target_user_id"])
    op.create_index("ix_admin_action_log_action", "admin_action_log", ["action"])
    op.create_index("ix_admin_action_log_created_at", "admin_action_log", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_admin_action_log_created_at", table_name="admin_action_log")
    op.drop_index("ix_admin_action_log_action", table_name="admin_action_log")
    op.drop_index("ix_admin_action_log_target_user_id", table_name="admin_action_log")
    op.drop_index("ix_admin_action_log_actor_id", table_name="admin_action_log")
    op.drop_table("admin_action_log")
