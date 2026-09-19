"""23.1 — Auth hardening security tables: login_attempts, refresh_tokens, user_sessions, user_2fa, audit_log

Revision ID: w3x4y5z6a7b8
Revises: u1v2w3x4y5z6
Create Date: 2026-09-19 11:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "w3x4y5z6a7b8"
down_revision = "u1v2w3x4y5z6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tablas de seguridad de 23.1. Son las unicas que crean login_attempts,
    # user_sessions y audit_log: la migracion 22.1 (u1v2w3x4y5z6) ya no las toca.
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False, index=True),
        sa.Column("ip", sa.String(45), nullable=False, index=True),
        sa.Column("success", sa.Boolean(), nullable=False, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            index=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create refresh_tokens table for opaque token rotation
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False, index=True),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("family_id", sa.UUID(), nullable=False, index=True),
        sa.Column(
            "issued_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("revoked", sa.Boolean(), default=False, nullable=False, index=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refresh_user_family", "refresh_tokens", ["user_id", "family_id"])

    # user_sessions con el esquema de app/models/auth.py
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False, index=True),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("ip", sa.String(45), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=False),
        sa.Column("device_name", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_activity",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
            nullable=False,
            index=True,
        ),
        sa.Column("revoked", sa.Boolean(), default=False, nullable=False, index=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create user_2fa table for TOTP setup
    op.create_table(
        "user_2fa",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False, unique=True, index=True),
        sa.Column("secret_key", sa.String(32), nullable=False),
        sa.Column("backup_codes", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("enabled", sa.Boolean(), default=False, nullable=False, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # audit_log con el esquema de app/models/auth.py
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.UUID(), nullable=True, index=True),
        sa.Column("action", sa.String(64), nullable=False, index=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            index=True,
        ),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("result", sa.String(16), default="success", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("event_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_user_timestamp", "audit_log", ["user_id", "timestamp"])
    op.create_index("ix_audit_action", "audit_log", ["action"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("user_2fa")
    op.drop_table("user_sessions")
    op.drop_table("refresh_tokens")
    op.drop_table("login_attempts")
