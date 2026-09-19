"""22.1 — Admin panel: campo `role` y tabla `gdpr_requests`.

Esta migración creaba también `promo_codes`, `credit_ledger` y `referrals`, que
`v0w1x2y3z4a5` (serie 29) vuelve a crear con el diseño definitivo. En producción
ambas corrieron —la segunda renombra o borra en tiempo de ejecución—, pero una
cadena no debe crear la misma tabla dos veces (`test_migrations_integrity`), así
que en bases nuevas las tres nacen solo en la 29.

Las tablas de seguridad (audit_log, login_attempts, user_sessions) las crea la
migración 23.1 `w3x4y5z6a7b8`, que es la que coincide con `app/models/auth.py`.
Crearlas aquí rompía `alembic upgrade head` (ver 24.0 en el ledger).

Revision ID: u1v2w3x4y5z6
Revises: t0u1v2w3x4y5
Create Date: 2026-09-19 09:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "u1v2w3x4y5z6"
down_revision = "t0u1v2w3x4y5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(32), nullable=False, server_default="user"))

    op.create_table(
        "gdpr_requests",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("request_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("export_url", sa.String(512), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gdpr_requests_user_id", "gdpr_requests", ["user_id"])
    op.create_index("ix_gdpr_requests_status", "gdpr_requests", ["status"])


def downgrade() -> None:
    op.drop_table("gdpr_requests")
    op.drop_column("users", "role")
