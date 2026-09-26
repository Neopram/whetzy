"""Integration tests for bootcamp endpoints (19.4)."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bootcamp import Bootcamp, BootcampWeek


@pytest.fixture
def _seed_bootcamp(db_session: AsyncSession):
    async def _create() -> Bootcamp:
        bc = Bootcamp(
            id=uuid.uuid4(),
            slug="test-boot",
            name_es="Bootcamp Test",
            name_en="Test Bootcamp",
            description_es="desc es",
            description_en="desc en",
            duration_weeks=2,
            daily_goal_minutes=30,
            order=1,
        )
        db_session.add(bc)
        for i in (1, 2):
            db_session.add(
                BootcampWeek(
                    id=uuid.uuid4(),
                    bootcamp_id=bc.id,
                    week_number=i,
                    track_id=f"track0{i}",
                    title_es=f"Semana {i}",
                    title_en=f"Week {i}",
                )
            )
        await db_session.commit()
        return bc

    return _create


@pytest.mark.asyncio
async def test_list_bootcamps(client: AsyncClient, db_session: AsyncSession, _seed_bootcamp):
    await _seed_bootcamp()
    resp = await client.get("/api/v1/bootcamps")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["slug"] == "test-boot"


@pytest.mark.asyncio
async def test_get_bootcamp_detail(client: AsyncClient, db_session: AsyncSession, _seed_bootcamp):
    await _seed_bootcamp()
    resp = await client.get("/api/v1/bootcamps/test-boot")
    assert resp.status_code == 200
    data = resp.json()
    assert data["slug"] == "test-boot"
    assert len(data["weeks"]) == 2
    assert data["weeks"][0]["week_number"] == 1


@pytest.mark.asyncio
async def test_get_bootcamp_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/bootcamps/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_enroll(client: AsyncClient, db_session: AsyncSession, _seed_bootcamp, auth_headers):
    await _seed_bootcamp()
    resp = await client.post("/api/v1/bootcamps/test-boot/enroll", headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["current_week"] == 1
    assert data["completed_at"] is None


@pytest.mark.asyncio
async def test_enroll_duplicate(client: AsyncClient, db_session: AsyncSession, _seed_bootcamp, auth_headers):
    await _seed_bootcamp()
    await client.post("/api/v1/bootcamps/test-boot/enroll", headers=auth_headers)
    resp = await client.post("/api/v1/bootcamps/test-boot/enroll", headers=auth_headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_progress(client: AsyncClient, db_session: AsyncSession, _seed_bootcamp, auth_headers):
    await _seed_bootcamp()
    await client.post("/api/v1/bootcamps/test-boot/enroll", headers=auth_headers)
    resp = await client.get("/api/v1/bootcamps/test-boot/progress", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["current_week"] == 1


@pytest.mark.asyncio
async def test_progress_not_enrolled(client: AsyncClient, db_session: AsyncSession, _seed_bootcamp, auth_headers):
    await _seed_bootcamp()
    resp = await client.get("/api/v1/bootcamps/test-boot/progress", headers=auth_headers)
    assert resp.status_code == 404
