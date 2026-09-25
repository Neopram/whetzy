"""Ligas opcionales (ledger 37.4): salir, no aparecer, no sumar, volver."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import League, LeagueEntry
from app.models.user import User
from app.services.gamification.service import (
    get_current_standings,
    get_or_create_current_entry,
)

URL = "/api/v1/league"


async def _seed_league(db: AsyncSession) -> League:
    league = League(id=f"lg_bronze_{uuid.uuid4().hex[:6]}", name="Bronce", tier="bronze", min_xp=0)
    db.add(league)
    await db.commit()
    return league


async def _other(db: AsyncSession, xp: int) -> User:
    u = User(id=uuid.uuid4(), email=f"o-{uuid.uuid4().hex[:6]}@example.com", username=f"o{uuid.uuid4().hex[:6]}",
             hashed_password="x", display_name="Otro")
    db.add(u)
    await db.commit()
    entry = await get_or_create_current_entry(db, u)
    assert entry is not None
    entry.xp_earned = xp
    await db.commit()
    return u


@pytest.mark.asyncio
async def test_opting_out_hides_me_and_shows_an_empty_board(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict[str, str]
) -> None:
    await _seed_league(db_session)
    other = await _other(db_session, 50)
    uid, other_id = user.id, other.id

    joined = (await client.get(f"{URL}/current", headers=auth_headers)).json()
    assert joined["participating"] is True
    assert {s["user_id"] for s in joined["standings"]} == {str(uid), str(other_id)}

    r = await client.put(f"{URL}/participation", json={"participate": False}, headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["participating"] is False
    assert r.json()["standings"] == []

    # El otro ya no me ve en su clasificación, aunque tengo entrada esta semana.
    other_view = await get_current_standings(db_session, await db_session.get(User, other_id))
    assert other_view is not None
    assert [s.user_id for s in other_view.standings] == [other_id]


@pytest.mark.asyncio
async def test_coming_back_restores_the_board(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict[str, str]
) -> None:
    await _seed_league(db_session)
    await client.put(f"{URL}/participation", json={"participate": False}, headers=auth_headers)
    r = await client.put(f"{URL}/participation", json={"participate": True}, headers=auth_headers)
    body = r.json()
    assert body["participating"] is True
    assert any(s["is_current_user"] for s in body["standings"])


@pytest.mark.asyncio
async def test_opted_out_user_creates_no_league_entry(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict[str, str]
) -> None:
    await _seed_league(db_session)
    uid = user.id
    await client.put(f"{URL}/participation", json={"participate": False}, headers=auth_headers)
    await client.get(f"{URL}/current", headers=auth_headers)
    rows = await db_session.execute(select(LeagueEntry).where(LeagueEntry.user_id == uid))
    assert rows.scalars().all() == []


@pytest.mark.asyncio
async def test_participation_requires_login(client: AsyncClient) -> None:
    r = await client.put(f"{URL}/participation", json={"participate": False})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_answering_while_opted_out_adds_no_league_xp(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict[str, str], content_seed: dict
) -> None:
    await _seed_league(db_session)
    uid = user.id
    await client.put(f"{URL}/participation", json={"participate": False}, headers=auth_headers)

    start = await client.post(
        "/api/v1/quiz/start", json={"skill_id": content_seed["skill_id"], "mode": "study"}, headers=auth_headers
    )
    assert start.status_code == 200, start.text
    body = start.json()
    r = await client.post(
        "/api/v1/quiz/answer",
        json={"session_id": body["session_id"], "question_id": body["question"]["id"],
              "selected_index": 0, "response_time_ms": 500},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text

    rows = await db_session.execute(select(LeagueEntry).where(LeagueEntry.user_id == uid))
    assert rows.scalars().all() == []
    assert (await db_session.get(User, uid)).total_xp >= 0  # el XP propio sigue su curso
