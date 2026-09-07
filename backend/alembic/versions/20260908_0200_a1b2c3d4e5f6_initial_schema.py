"""initial_schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-09-08 02:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── content hierarchy ──────────────────────────────────────────────────────
    op.create_table(
        "tracks",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("name_es", sa.String(150), nullable=False),
        sa.Column("name_en", sa.String(150), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("icon", sa.String(16), nullable=False),
        sa.Column("color", sa.String(16), nullable=False),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "modules",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("track_id", sa.String(64), nullable=False),
        sa.Column("name_es", sa.String(150), nullable=False),
        sa.Column("name_en", sa.String(150), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("description_es", sa.Text(), nullable=False),
        sa.Column("description_en", sa.Text(), nullable=False),
        sa.Column("min_mastery_to_unlock", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_modules_track_id", "modules", ["track_id"])

    op.create_table(
        "skills",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("module_id", sa.String(64), nullable=False),
        sa.Column("name_es", sa.String(150), nullable=False),
        sa.Column("name_en", sa.String(150), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_skills_module_id", "skills", ["module_id"])

    op.create_table(
        "questions",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("skill_id", sa.String(64), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("difficulty_tier", sa.String(20), nullable=False),
        sa.Column("question_es", sa.Text(), nullable=False),
        sa.Column("question_en", sa.Text(), nullable=False),
        sa.Column("options_es", sa.JSON(), nullable=True),
        sa.Column("options_en", sa.JSON(), nullable=True),
        sa.Column("correct_index", sa.Integer(), nullable=True),
        sa.Column("correct_answer_es", sa.Text(), nullable=True),
        sa.Column("correct_answer_en", sa.Text(), nullable=True),
        sa.Column("explanation_es", sa.Text(), nullable=False),
        sa.Column("explanation_en", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("elo_rating", sa.Float(), nullable=False),
        sa.Column("discrimination", sa.Float(), nullable=False),
        sa.Column("guessing", sa.Float(), nullable=False),
        sa.Column("expected_time_ms", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_questions_skill_id", "questions", ["skill_id"])

    op.create_table(
        "glossary_terms",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("track_id", sa.String(64), nullable=False),
        sa.Column("term_es", sa.String(200), nullable=False),
        sa.Column("term_en", sa.String(200), nullable=False),
        sa.Column("definition_es", sa.Text(), nullable=False),
        sa.Column("definition_en", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_glossary_terms_track_id", "glossary_terms", ["track_id"])

    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("avatar_emoji", sa.String(16), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("total_xp", sa.Integer(), nullable=False),
        sa.Column("current_streak", sa.Integer(), nullable=False),
        sa.Column("max_streak", sa.Integer(), nullable=False),
        sa.Column("streak_freeze_available", sa.Integer(), nullable=False),
        sa.Column("last_active", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_premium", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("language", sa.String(2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # ── gamification: static tables ───────────────────────────────────────────
    op.create_table(
        "leagues",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("tier", sa.String(20), nullable=False),
        sa.Column("min_xp", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "badges",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("name_es", sa.String(150), nullable=False),
        sa.Column("name_en", sa.String(150), nullable=False),
        sa.Column("icon", sa.String(16), nullable=False),
        sa.Column("description_es", sa.String(255), nullable=False),
        sa.Column("description_en", sa.String(255), nullable=False),
        sa.Column("criteria_type", sa.String(50), nullable=False),
        sa.Column("criteria_value", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "missions",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("target_value", sa.Integer(), nullable=False),
        sa.Column("xp_reward", sa.Integer(), nullable=False),
        sa.Column("name_es", sa.String(150), nullable=False),
        sa.Column("name_en", sa.String(150), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── gamification: per-user tables ─────────────────────────────────────────
    op.create_table(
        "user_skill_states",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", sa.String(64), nullable=False),
        sa.Column("p_known", sa.Float(), nullable=False),
        sa.Column("elo_rating", sa.Float(), nullable=False),
        sa.Column("fsrs_stability", sa.Float(), nullable=False),
        sa.Column("fsrs_difficulty", sa.Float(), nullable=False),
        sa.Column("fsrs_due", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "skill_id", name="uq_user_skill_state"),
    )
    op.create_index("ix_user_skill_states_user_id", "user_skill_states", ["user_id"])
    op.create_index("ix_user_skill_states_skill_id", "user_skill_states", ["skill_id"])

    op.create_table(
        "user_badges",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("badge_id", sa.String(64), nullable=False),
        sa.Column(
            "earned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["badge_id"], ["badges.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )
    op.create_index("ix_user_badges_user_id", "user_badges", ["user_id"])
    op.create_index("ix_user_badges_badge_id", "user_badges", ["badge_id"])

    op.create_table(
        "league_entries",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("league_id", sa.String(64), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("xp_earned", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "league_id", "week_start", name="uq_league_entry"),
    )
    op.create_index("ix_league_entries_user_id", "league_entries", ["user_id"])
    op.create_index("ix_league_entries_league_id", "league_entries", ["league_id"])
    op.create_index("ix_league_entries_week_start", "league_entries", ["week_start"])

    op.create_table(
        "user_missions",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("mission_id", sa.String(64), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["mission_id"], ["missions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "mission_id", "date", name="uq_user_mission_date"),
    )
    op.create_index("ix_user_missions_user_id", "user_missions", ["user_id"])
    op.create_index("ix_user_missions_mission_id", "user_missions", ["mission_id"])
    op.create_index("ix_user_missions_date", "user_missions", ["date"])

    # ── sessions & responses ───────────────────────────────────────────────────
    op.create_table(
        "study_sessions",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("questions_answered", sa.Integer(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("xp_earned", sa.Integer(), nullable=False),
        sa.Column("max_combo", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_study_sessions_user_id", "study_sessions", ["user_id"])

    op.create_table(
        "responses",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", sa.String(64), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("grade", sa.Integer(), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["study_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_responses_session_id", "responses", ["session_id"])
    op.create_index("ix_responses_question_id", "responses", ["question_id"])


def downgrade() -> None:
    op.drop_index("ix_responses_question_id", table_name="responses")
    op.drop_index("ix_responses_session_id", table_name="responses")
    op.drop_table("responses")
    op.drop_index("ix_study_sessions_user_id", table_name="study_sessions")
    op.drop_table("study_sessions")
    op.drop_index("ix_user_missions_date", table_name="user_missions")
    op.drop_index("ix_user_missions_mission_id", table_name="user_missions")
    op.drop_index("ix_user_missions_user_id", table_name="user_missions")
    op.drop_table("user_missions")
    op.drop_index("ix_league_entries_week_start", table_name="league_entries")
    op.drop_index("ix_league_entries_league_id", table_name="league_entries")
    op.drop_index("ix_league_entries_user_id", table_name="league_entries")
    op.drop_table("league_entries")
    op.drop_index("ix_user_badges_badge_id", table_name="user_badges")
    op.drop_index("ix_user_badges_user_id", table_name="user_badges")
    op.drop_table("user_badges")
    op.drop_index("ix_user_skill_states_skill_id", table_name="user_skill_states")
    op.drop_index("ix_user_skill_states_user_id", table_name="user_skill_states")
    op.drop_table("user_skill_states")
    op.drop_table("missions")
    op.drop_table("badges")
    op.drop_table("leagues")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_glossary_terms_track_id", table_name="glossary_terms")
    op.drop_table("glossary_terms")
    op.drop_index("ix_questions_skill_id", table_name="questions")
    op.drop_table("questions")
    op.drop_index("ix_skills_module_id", table_name="skills")
    op.drop_table("skills")
    op.drop_index("ix_modules_track_id", table_name="modules")
    op.drop_table("modules")
    op.drop_table("tracks")
