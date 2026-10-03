"""newsletter_subscribers: alta pública con doble opt-in vía Resend (26.10, H.30).

Tabla independiente de ``users`` — cualquiera se suscribe sin tener cuenta en
Whetzy. El enlace de confirmación/baja es un JWT firmado (``create_unsubscribe_
token``), no un secreto guardado aquí: no hace falta columna de token.
``last_sent_at`` acota cuántos correos de confirmación puede forzar un POST
repetido a la misma dirección (revisión de [S5], PR #94).

Revision ID: 20261002_newsletter_subscribers
Revises: 20261002_mastery_reports

NOTA (pendiente, no aplicar todavía): esta revisión debe apuntar en cambio a
``20261002_user_moderation`` (PR #92, [MIGRACIÓN] de S1) en cuanto esa migración
esté en master — y las tres líneas del HEAD de Alembic pasan a 53. #92 sigue
abierto a fecha de este commit; aplicar el cambio de ``down_revision`` antes de
que se fusione dejaría una cadena que no existe todavía.
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
