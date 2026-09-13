"""Tests for the gamification seeder.

`seed_gamification` runs on deploy next to `load_content`. Its reference rows
are what the mission/badge engine matches against, so a typo in a `type` or
`criteria_type` here silently disables a whole mission — these tests pin the
contract against the consumers rather than just re-asserting the literals.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.models.gamification import Badge, League, Mission
from app.services import seed as seed_service
from app.services.seed import BADGES, LEAGUES, MISSIONS, seed_gamification

# Mission types `apply_quiz_event` actually handles (see seed.py's own comment).
HANDLED_MISSION_TYPES = {
    "questions_answered",
    "correct_answers",
    "xp_earned",
    "perfect_combo",
}


class TestSeedGamification:
    @pytest.mark.asyncio
    async def test_returns_counts(self, db_session) -> None:
        stats = await seed_gamification(db_session)
        assert stats == {
            "leagues": len(LEAGUES),
            "missions": len(MISSIONS),
            "badges": len(BADGES),
        }

    @pytest.mark.asyncio
    async def test_inserts_every_row(self, db_session) -> None:
        await seed_gamification(db_session)
        assert await db_session.scalar(select(func.count(League.id))) == len(LEAGUES)
        assert await db_session.scalar(select(func.count(Mission.id))) == len(MISSIONS)
        assert await db_session.scalar(select(func.count(Badge.id))) == len(BADGES)

    @pytest.mark.asyncio
    async def test_league_fields_land(self, db_session) -> None:
        await seed_gamification(db_session)
        bronze = await db_session.get(League, "bronze")
        diamond = await db_session.get(League, "diamond")
        assert bronze is not None and diamond is not None
        assert bronze.tier == "bronze"
        assert bronze.min_xp == 0
        assert diamond.min_xp == 10000

    @pytest.mark.asyncio
    async def test_mission_fields_land(self, db_session) -> None:
        await seed_gamification(db_session)
        m = await db_session.get(Mission, "m1_questions")
        assert m is not None
        assert m.type == "questions_answered"
        assert m.target_value == 10
        assert m.xp_reward == 30
        assert m.name_es == "Responde 10 preguntas"
        assert m.name_en == "Answer 10 questions"

    @pytest.mark.asyncio
    async def test_badge_fields_land(self, db_session) -> None:
        await seed_gamification(db_session)
        b = await db_session.get(Badge, "streak_7")
        assert b is not None
        assert b.criteria_type == "streak"
        assert b.criteria_value == 7
        assert b.icon == "🔥"
        assert b.name_es and b.name_en

    @pytest.mark.asyncio
    async def test_is_idempotent(self, db_session) -> None:
        first = await seed_gamification(db_session)
        second = await seed_gamification(db_session)
        assert first == second
        assert await db_session.scalar(select(func.count(League.id))) == len(LEAGUES)
        assert await db_session.scalar(select(func.count(Mission.id))) == len(MISSIONS)
        assert await db_session.scalar(select(func.count(Badge.id))) == len(BADGES)

    @pytest.mark.asyncio
    async def test_rerun_repairs_a_drifted_row(self, db_session) -> None:
        """Upsert, not insert-if-missing: a hand-edited row is corrected."""
        await seed_gamification(db_session)
        gold = await db_session.get(League, "gold")
        assert gold is not None
        gold.min_xp = 1
        await db_session.commit()

        await seed_gamification(db_session)
        gold = await db_session.get(League, "gold")
        assert gold is not None
        assert gold.min_xp == 2000

    @pytest.mark.asyncio
    async def test_id_is_never_overwritten_by_the_setattr_loop(self, db_session) -> None:
        await seed_gamification(db_session)
        ids = {m.id for m in (await db_session.execute(select(Mission))).scalars().all()}
        assert ids == {d["id"] for d in MISSIONS}


class TestReferenceDataContract:
    """These guard the data, not the code path — a bad literal here is a
    silently dead mission or badge in production."""

    def test_ids_are_unique(self) -> None:
        for rows in (LEAGUES, MISSIONS, BADGES):
            ids = [r["id"] for r in rows]
            assert len(ids) == len(set(ids)), ids

    def test_every_mission_type_is_handled_by_the_engine(self) -> None:
        for m in MISSIONS:
            assert m["type"] in HANDLED_MISSION_TYPES, m["id"]

    def test_leagues_are_ordered_by_min_xp(self) -> None:
        xps = [league["min_xp"] for league in LEAGUES]
        assert xps == sorted(xps)
        assert len(set(xps)) == len(xps)

    def test_lowest_league_starts_at_zero(self) -> None:
        # A new user with 0 XP must land somewhere.
        assert min(league["min_xp"] for league in LEAGUES) == 0

    def test_league_tier_matches_its_id(self) -> None:
        for league in LEAGUES:
            assert league["tier"] == league["id"]

    def test_missions_and_badges_are_bilingual(self) -> None:
        """Red line 3: no user-visible string ships in one language only."""
        for m in MISSIONS:
            assert m["name_es"] and m["name_en"]
        for b in BADGES:
            assert b["name_es"] and b["name_en"]
            assert b["description_es"] and b["description_en"]

    def test_positive_targets_and_rewards(self) -> None:
        for m in MISSIONS:
            assert m["target_value"] > 0
            assert m["xp_reward"] > 0
        for b in BADGES:
            assert b["criteria_value"] > 0

    def test_correct_answers_target_does_not_exceed_questions_target(self) -> None:
        """An unreachable daily mission is a dark pattern (red line 7)."""
        answered = next(m for m in MISSIONS if m["type"] == "questions_answered")
        correct = next(m for m in MISSIONS if m["type"] == "correct_answers")
        assert correct["target_value"] <= answered["target_value"]

    def test_service_picks_first_three_missions_by_id(self) -> None:
        """seed.py documents that the service takes the first 3 by id, so the
        id prefixes must sort the intended daily mix to the front."""
        by_id = sorted(m["id"] for m in MISSIONS)
        chosen = {m["type"] for m in MISSIONS if m["id"] in by_id[:3]}
        assert chosen == {"questions_answered", "correct_answers", "perfect_combo"}


class TestMain:
    @pytest.mark.asyncio
    async def test_main_seeds_and_reports(
        self, db_session, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        called: dict[str, bool] = {"init": False}

        async def fake_init_db() -> None:
            called["init"] = True

        class _SessionCtx:
            async def __aenter__(self):
                return db_session

            async def __aexit__(self, *exc: object) -> bool:
                return False

        monkeypatch.setattr(seed_service, "init_db", fake_init_db)
        monkeypatch.setattr(seed_service, "AsyncSessionLocal", lambda: _SessionCtx())

        await seed_service.main()

        assert called["init"] is True
        assert "Gamification seeded:" in capsys.readouterr().out
