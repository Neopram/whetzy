"""newsletter_subscribers: alta pública con doble opt-in vía Resend (26.10, H.30).

Tabla independiente de ``users`` — cualquiera se suscribe sin tener cuenta en
Whetzy. El enlace de confirmación/baja es un JWT firmado (``create_unsubscribe_
token``), no un secreto guardado aquí: no hace falta columna de token.
``last_sent_at`` acota cuántos correos de confirmación puede forzar un POST
repetido a la misma dirección (revisión de [S5], PR #94).

Revision ID: 20261002_newsletter_subscribers
Revises: 20261002_user_moderation

Encadenada tras ``20261002_user_moderation`` (PR #92, [S1]) en cuanto ese PR
se fusionó a master (2026-10-03) — las dos migraciones reclamaban el mismo
``down_revision`` (``20261002_mastery_reports``) mientras ambos PR estaban
abiertos a la vez; #92 fusionó primero, así que esta se reencadena sobre él.
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261002_newsletter_subscribers"
down_revision = "20261002_user_moderation"
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
        sa.Column("unsubscribed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_newsletter_subscribers_email", "newsletter_subscribers", ["email"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_newsletter_subscribers_email", table_name="newsletter_subscribers")
    op.drop_table("newsletter_subscribers")
