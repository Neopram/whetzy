"""E1: duel answers update UserSkillState (BKT/Elo/FSRS).

Before: answering a duel question stored the result as JSON in `duel.answers`
but never touched UserSkillState — skill mastery stayed stale after duels.
After: each answered question runs the same BKT/Elo/FSRS update path as
a regular quiz answer (without a Response row, which requires session_id).
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserSkillState


async def _register(client: AsyncClient, tag: str) -> dict[str, str]:
    u = f"e1{tag}{uuid.uuid4().hex[:8]}"
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{u}@example.com",
            "username": u,
            "display_name": u,
            "password": "duel-e1-pass",
            "language": "es",
            "age_confirmed": True,
        },
    )
    assert r.status_code in (200, 201), r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_duel_answer_updates_skill_state(client: AsyncClient, db_session: AsyncSession) -> None:
    """Answering a duel question changes p_known/attempts in UserSkillState."""
    auth_a = await _register(client, "a")
    auth_b = await _register(client, "b")

    # Get user_id for challenger
    me_r = await client.get("/api/v1/auth/me", headers=auth_a)
    assert me_r.status_code == 200
    user_a_id = uuid.UUID(me_r.json()["id"])

    # Get opponent username
    me_b = await client.get("/api/v1/auth/me", headers=auth_b)
    opponent_username = me_b.json()["username"]

    # Challenger needs at least one skill with attempts so _pick_skill works;
    # find a skill_id from any available question instead.
    questions_r = await client.get("/api/v1/quiz/questions?limit=10", headers=auth_a)
    if questions_r.status_code != 200 or not questions_r.json():
        # If no questions are available, skip gracefully.
        pytest.skip("No questions available in test DB")

    # Find a skill_id that has enough MCQ questions for a duel (5 required).
    # Use the challenge endpoint directly with skill_id to avoid _pick_skill
    # needing a prior skill attempt.
    skill_id: str | None = None
    seen_skills: set[str] = set()
    for q in questions_r.json():
        sid = q.get("skill_id")
        if sid and sid not in seen_skills:
            seen_skills.add(sid)
            ch_r = await client.post(
                "/api/v1/duels/challenge",
                json={"opponent_username": opponent_username, "skill_id": sid},
                headers=auth_a,
            )
            if ch_r.status_code == 201:
                skill_id = sid
                duel_data = ch_r.json()
                break

    if skill_id is None:
        pytest.skip("Could not create a duel with available test questions")

    duel_id = duel_data["duel_id"]
    questions = duel_data["questions"]

    # Record p_known BEFORE answering
    await db_session.rollback()  # ensure fresh view
    state_before = (
        await db_session.execute(
            select(UserSkillState).where(
                UserSkillState.user_id == user_a_id,
                UserSkillState.skill_id == skill_id,
            )
        )
    ).scalar_one_or_none()
    attempts_before = state_before.attempts if state_before else 0

    # Answer first question
    q0 = questions[0]
    ans_r = await client.post(
        f"/api/v1/duels/{duel_id}/answer",
        json={
            "question_id": q0["id"],
            "selected_index": 0,
            "response_time_ms": 3000,
        },
        headers=auth_a,
    )
    assert ans_r.status_code == 200, ans_r.text

    # Re-read state — attempts must have incremented
    await db_session.rollback()
    state_after = (
        await db_session.execute(
            select(UserSkillState).where(
                UserSkillState.user_id == user_a_id,
                UserSkillState.skill_id == skill_id,
            )
        )
    ).scalar_one_or_none()

    assert state_after is not None, "UserSkillState row was not created after duel answer"
    assert state_after.attempts == attempts_before + 1, (
        f"Expected attempts={attempts_before + 1}, got {state_after.attempts} — "
        "duel answer did not update UserSkillState"
    )
