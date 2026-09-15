"""Track final exams, module test-out and certificates (17.2).

`mock_exam_attempts` gains three columns rather than getting a sibling table:
a certification mock, a track final and a test-out are the same object - a
frozen question draw with a server-side deadline - and differ only in how they
are blueprinted and what passing earns. `kind` says which, `module_id` scopes a
test-out to its module, and `pass_pct` freezes the bar at start so a later
change to the threshold cannot retroactively turn yesterday's pass into a fail.

`pass_pct` is deliberately nullable: the certification mock has none. It reports
a raw percentage and refuses to declare a pass against AWS's scaled score, which
we have no basis to compute (see services/mock_exam.py).

`certificates.code` is the public, unguessable handle behind the unauthenticated
verification endpoint, so it is unique and indexed.

Revision ID: r8s9t0u1v2w3
Revises: q7r8s9t0u1v2
Create Date: 2026-09-15 19:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = 'r8s9t0u1v2w3'
down_revision = 'q7r8s9t0u1v2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text(
        "ALTER TABLE mock_exam_attempts ADD COLUMN IF NOT EXISTS kind VARCHAR(20) "
        "NOT NULL DEFAULT 'certification'"
    ))
    op.execute(sa.text(
        "ALTER TABLE mock_exam_attempts ADD COLUMN IF NOT EXISTS module_id VARCHAR(64) "
        "REFERENCES modules(id) ON DELETE CASCADE"
    ))
    op.execute(sa.text(
        "ALTER TABLE mock_exam_attempts ADD COLUMN IF NOT EXISTS pass_pct DOUBLE PRECISION"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_mock_exam_attempts_kind "
        "ON mock_exam_attempts (kind)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_mock_exam_attempts_module_id "
        "ON mock_exam_attempts (module_id)"
    ))

    op.execute(sa.text(
        """
        CREATE TABLE IF NOT EXISTS certificates (
            id UUID PRIMARY KEY,
            code VARCHAR(64) NOT NULL UNIQUE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            track_id VARCHAR(64) NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
            attempt_id UUID NOT NULL REFERENCES mock_exam_attempts(id) ON DELETE CASCADE,
            score_pct DOUBLE PRECISION NOT NULL,
            questions INTEGER NOT NULL,
            issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            revoked BOOLEAN NOT NULL DEFAULT false
        )
        """
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_certificates_code ON certificates (code)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_certificates_user_id ON certificates (user_id)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_certificates_track_id ON certificates (track_id)"
    ))
    # One certificate per learner per track. The service checks for an existing
    # one before minting, but two submissions racing would both pass that check;
    # the constraint is what actually makes it true.
    op.execute(sa.text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_certificate_user_track "
        "ON certificates (user_id, track_id)"
    ))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS certificates"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_mock_exam_attempts_module_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_mock_exam_attempts_kind"))
    op.execute(sa.text("ALTER TABLE mock_exam_attempts DROP COLUMN IF EXISTS pass_pct"))
    op.execute(sa.text("ALTER TABLE mock_exam_attempts DROP COLUMN IF EXISTS module_id"))
    op.execute(sa.text("ALTER TABLE mock_exam_attempts DROP COLUMN IF EXISTS kind"))
