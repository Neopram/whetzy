"""GET /api/v1/content/tracks (task Q.14).

The point of this endpoint is that the client stops keeping its own copy of the
track list. The test that matters is therefore not "it returns 200" but "it
returns what the content actually contains" - the AWS certification track was
loaded, stored and served by the API for a whole session while remaining
invisible in the app, because the app had its own hardcoded list of seven.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Track
from app.services.content_loader import load_content

BASE = "/api/v1/content/tracks"


@pytest.mark.asyncio
async def test_serves_every_track_the_content_defines(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CONTENT_DIR", raising=False)
    await load_content(db_session)

    loaded = await db_session.scalar(select(func.count(Track.id)))
    res = await client.get(BASE, headers=auth_headers)
    assert res.status_code == 200, res.text
    assert len(res.json()) == loaded, (
        "the API must serve every loaded track; a mismatch is how a track ends "
        "up shipped in the content and missing from the app"
    )


@pytest.mark.asyncio
async def test_exposes_the_exam_blueprint_for_certification_tracks(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The client decides whether to offer a mock exam from these fields, so a
    certification track that arrives looking like a learning track silently
    loses its exam."""
    monkeypatch.delenv("CONTENT_DIR", raising=False)
    await load_content(db_session)

    tracks = {t["id"]: t for t in (await client.get(BASE, headers=auth_headers)).json()}

    aws = tracks["track08"]
    assert aws["is_certification"] is True
    assert aws["cert_provider"] == "AWS"
    assert aws["exam_question_count"] == 65
    assert aws["exam_duration_minutes"] == 90

    learning = tracks["track01"]
    assert learning["is_certification"] is False
    assert learning["exam_question_count"] is None


@pytest.mark.asyncio
async def test_tracks_come_back_in_curriculum_order(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CONTENT_DIR", raising=False)
    await load_content(db_session)

    orders = [t["order"] for t in (await client.get(BASE, headers=auth_headers)).json()]
    assert orders == sorted(orders)


@pytest.mark.asyncio
async def test_requires_authentication(client: AsyncClient) -> None:
    res = await client.get(BASE)
    assert res.status_code in (401, 403)
