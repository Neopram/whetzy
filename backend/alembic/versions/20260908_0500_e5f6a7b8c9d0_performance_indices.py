"""performance_indices

Composite indices for the hottest queries measured via EXPLAIN ANALYZE:

  /quiz/start         → questions WHERE skill_id=? ORDER BY elo_rating
  /progress/skills    → user_skill_states WHERE user_id=? (join to skills.module_id)
  /progress/dashboard → study_sessions WHERE user_id=?, responses aggregation
  league standings    → league_entries WHERE league_id=? AND week_start=? ORDER BY xp_earned DESC
  daily missions      → user_missions WHERE user_id=? AND date=?

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-08 05:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Quiz engine: select questions by skill ordered by Elo band.
    op.create_index(
        "ix_questions_skill_elo",
        "questions",
        ["skill_id", "elo_rating"],
    )

    # Quiz engine: filter by question type (e.g. only MCQ, skip exec types).
    op.create_index(
        "ix_questions_type",
        "questions",
        ["type"],
    )

    # Progress: scan responses for a session (already indexed by session_id),
    # but the aggregation filters by correct — this covering index avoids heap fetch.
    op.create_index(
        "ix_responses_session_correct",
        "responses",
        ["session_id", "correct"],
    )

    # Progress: recent session history per user ordered by start time.
    op.create_index(
        "ix_study_sessions_user_started",
        "study_sessions",
        ["user_id", "started_at"],
    )

    # League standings: weekly leaderboard (league + week → sort by xp DESC).
    op.create_index(
        "ix_league_entries_league_week_xp",
        "league_entries",
        ["league_id", "week_start", "xp_earned"],
    )

    # Daily missions: user's missions for a given date.
    op.create_index(
        "ix_user_missions_user_date",
        "user_missions",
        ["user_id", "date"],
    )

    # DKT / progress: look up all skill states for a user in a specific skill.
    # The unique constraint (user_id, skill_id) already acts as an index,
    # but adding (skill_id, user_id) order helps FK-join from skills side.
    op.create_index(
        "ix_user_skill_states_skill_user",
        "user_skill_states",
        ["skill_id", "user_id"],
    )

    # FSRS due-review scan: skills due before now (spaced-repetition scheduler).
    op.create_index(
        "ix_user_skill_states_due",
        "user_skill_states",
        ["user_id", "fsrs_due"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_skill_states_due", table_name="user_skill_states")
    op.drop_index("ix_user_skill_states_skill_user", table_name="user_skill_states")
    op.drop_index("ix_user_missions_user_date", table_name="user_missions")
    op.drop_index("ix_league_entries_league_week_xp", table_name="league_entries")
    op.drop_index("ix_study_sessions_user_started", table_name="study_sessions")
    op.drop_index("ix_responses_session_correct", table_name="responses")
    op.drop_index("ix_questions_type", table_name="questions")
    op.drop_index("ix_questions_skill_elo", table_name="questions")
