"""Add project tables (18.8 / 19.6).

Revision ID: 20260926_projects
Revises: 20260926_bootcamps
Create Date: 2026-09-26
"""

import sqlalchemy as sa

from alembic import op

revision = "20260926_projects"
down_revision = "20260926_bootcamps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.String(128), unique=True, nullable=False, index=True),
        sa.Column("track_id", sa.String(64), nullable=False, index=True),
        sa.Column(
            "runtime",
            sa.Enum("python", "sql", "js", name="project_runtime"),
            nullable=False,
        ),
        sa.Column("name_es", sa.String(300), nullable=False),
        sa.Column("name_en", sa.String(300), nullable=False),
        sa.Column("description_es", sa.Text(), nullable=False, server_default=""),
        sa.Column("description_en", sa.Text(), nullable=False, server_default=""),
        sa.Column("difficulty", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_url", sa.String(500), nullable=False, server_default=""),
        sa.Column("source_license", sa.String(64), nullable=False, server_default="MIT"),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "project_steps",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("title_es", sa.String(300), nullable=False),
        sa.Column("title_en", sa.String(300), nullable=False),
        sa.Column("instructions_es", sa.Text(), nullable=False, server_default=""),
        sa.Column("instructions_en", sa.Text(), nullable=False, server_default=""),
        sa.Column("starter_code", sa.Text(), nullable=False, server_default=""),
        sa.Column("test_code", sa.Text(), nullable=False, server_default=""),
        sa.Column("solution_code", sa.Text(), nullable=False, server_default=""),
    )

    op.create_table(
        "project_submissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("project_submissions")
    op.drop_table("project_steps")
    op.drop_table("projects")
    op.execute("DROP TYPE IF EXISTS project_runtime")
