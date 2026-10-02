"""newsletter_subscribers: alta pública con doble opt-in vía Resend (26.10, H.30).

Tabla independiente de ``users`` — cualquiera se suscribe sin tener cuenta en
Whetzy. ``token_hash`` guarda el SHA-256 del token que viaja en el correo de
confirmación; se conserva tras confirmar porque el mismo enlace sirve de baja.

Revision ID: 20261002_newsletter_subscribers
Revises: 20261002_mastery_reports
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261002_newsletter_subscribers"
down_revision = "20261002_mastery_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "newsletter_subscribers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("language", sa.String(length=2), nullable=False),
        sa.Column("confirmed", sa.Boolean(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("unsubscribed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_newsletter_subscribers_email", "newsletter_subscribers", ["email"], unique=True
    )
    op.create_index(
        "ix_newsletter_subscribers_token_hash",
        "newsletter_subscribers",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_newsletter_subscribers_token_hash", table_name="newsletter_subscribers")
    op.drop_index("ix_newsletter_subscribers_email", table_name="newsletter_subscribers")
    op.drop_table("newsletter_subscribers")
