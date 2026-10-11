"""oauth_states.code_verifier: PKCE para el login social (S.14, plan de la
noche 2026-10-04).

El `state` de OAuth vivía solo en la base de datos, sin atar a ninguna
cookie del navegador que lo inició: un `state` válido y sin consumir se
aceptaba desde cualquier navegador, no solo el que lo pidió. Y no existía
PKCE (RFC 7636) en absoluto — ni `code_verifier` ni `code_challenge`.

Esta columna guarda el `code_verifier` generado en `/start`, para mandarlo
en el intercambio del código por el token en `/callback` (el `code_challenge`
derivado de él va en la URL de autorización, no se guarda). El atado a
cookie no necesita columna nueva: usa la misma cookie HttpOnly de siempre.

Nullable y sin backfill a propósito: una fila de `oauth_states` en vuelo en
el momento del despliegue (vida máxima 10 minutos) nunca tuvo PKCE, así que
un `code_verifier` NULL en ese intento concreto simplemente no lo manda en
el intercambio — el proveedor no lo exige si la autorización no llevó
`code_challenge`, y ese login en concreto completa como antes.

El ID de esta revisión está a propósito corto: `alembic_version` usa
`varchar(32)` y `20261004_study_session_current_question` (39 caracteres)
tumbó producción el 2026-10-10 (#165, hotfix) al no caber en el UPDATE del
alembic_version tras el upgrade() — renombrada a `20261004_current_question_id`
(28 caracteres), que es de lo que cuelga esta.

Revision ID: 20261010_oauth_pkce
Revises: 20261004_current_question_id
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261010_oauth_pkce"
down_revision = "20261004_current_question_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "oauth_states",
        sa.Column("code_verifier", sa.String(length=128), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("oauth_states", "code_verifier")
