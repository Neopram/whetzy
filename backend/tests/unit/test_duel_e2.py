"""E2: duel result includes weak_skill_id for the loser, None for the winner.

After a duel completes, GET /{id}/result returns `weak_skill_id` equal to the
duel's skill_id when the requesting player did not win (lost or drew), and None
when they won.
"""
import uuid

import pytest
from httpx import AsyncClient


async def _register(client: AsyncClient, tag: str) -> tuple[dict[str, str], str]:
    u = f"e2{tag}{uuid.uuid4().hex[:8]}"
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{u}@example.com",
            "username": u,
            "display_name": u,
            "password": "duel-e2-pass",
            "language": "es",
            "age_confirmed": True,
        },
    )
    assert r.status_code in (200, 201), r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}, u


async def _find_skill_and_create_duel(
    client: AsyncClient, auth_a: dict, opponent_username: str
) -> tuple[str, list] | None:
    questions_r = await client.get("/api/v1/quiz/questions?limit=10", headers=auth_a)
    if questions_r.status_code != 200 or not questions_r.json():
        return None
    seen: set[str] = set()
    for q in questions_r.json():
        sid = q.get("skill_id")
        if sid and sid not in seen:
            seen.add(sid)
            ch_r = await client.post(
                "/api/v1/duels/challenge",
                json={"opponent_username": opponent_username, "skill_id": sid},
                headers=auth_a,
            )
            if ch_r.status_code == 201:
                data = ch_r.json()
                return data["duel_id"], data["questions"]
    return None


async def _answer_all(client: AsyncClient, auth: dict, duel_id: str, questions: list, selected: int = 0) -> None:
    for q in questions:
        r = await client.post(
            f"/api/v1/duels/{duel_id}/answer",
            json={"question_id": q["id"], "selected_index": selected, "response_time_ms": 1000},
            headers=auth,
        )
        assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_duel_result_weak_skill_for_loser(client: AsyncClient) -> None:
    """Loser gets weak_skill_id == duel's skill_id; winner gets None."""
    auth_a, _ = await _register(client, "a")
    auth_b, username_b = await _register(client, "b")

    result = await _find_skill_and_create_duel(client, auth_a, username_b)
    if result is None:
        pytest.skip("No questions available in test DB")

    duel_id, questions = result

    # Challenger answers all wrong (index 99 → always wrong since options are 0-based)
    await _answer_all(client, auth_a, duel_id, questions, selected=99)

    # Opponent joins and answers all correct (index 0 — first option)
    join_r = await client.get(f"/api/v1/duels/{duel_id}/join", headers=auth_b)
    assert join_r.status_code == 200
    opp_questions = join_r.json()["questions"]
    await _answer_all(client, auth_b, duel_id, opp_questions, selected=0)

    # Challenger (loser) should get weak_skill_id == skill_id
    result_a = await client.get(f"/api/v1/duels/{duel_id}/result", headers=auth_a)
    assert result_a.status_code == 200, result_a.text
    body_a = result_a.json()
    assert body_a["weak_skill_id"] is not None, "Loser must receive weak_skill_id"
    assert body_a["weak_skill_id"] == body_a["skill_id"]

    # Opponent (winner) should get weak_skill_id == None
    result_b = await client.get(f"/api/v1/duels/{duel_id}/result", headers=auth_b)
    assert result_b.status_code == 200, result_b.text
    body_b = result_b.json()
    # winner_id must be opponent
    assert body_b["winner_id"] is not None
    assert body_b["weak_skill_id"] is None, "Winner must receive weak_skill_id=None"
