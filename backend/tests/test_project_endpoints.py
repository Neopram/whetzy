"""Smoke tests for project endpoints (18.8 / 19.6)."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStep


@pytest.mark.asyncio
async def test_list_projects_empty(client: AsyncClient) -> None:
    r = await client.get("/api/v1/projects")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient) -> None:
    r = await client.get("/api/v1/projects/nonexistent")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_project_crud(client: AsyncClient, db_session: AsyncSession, auth_headers: dict[str, str]) -> None:
    project = Project(
        id=uuid.uuid4(),
        slug="test-hello-world",
        track_id="track01",
        runtime="python",
        name_es="Hola Mundo",
        name_en="Hello World",
        description_es="Primer proyecto",
        description_en="First project",
        difficulty=1,
        order=1,
    )
    db_session.add(project)

    step1 = ProjectStep(
        id=uuid.uuid4(),
        project_id=project.id,
        step_number=1,
        title_es="Paso 1",
        title_en="Step 1",
        instructions_es="Escribe print('hola')",
        instructions_en="Write print('hello')",
        starter_code="# your code here",
        test_code="assert True",
    )
    db_session.add(step1)
    await db_session.commit()

    r = await client.get("/api/v1/projects")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert any(p["slug"] == "test-hello-world" for p in data)

    r = await client.get("/api/v1/projects/test-hello-world")
    assert r.status_code == 200
    detail = r.json()
    assert detail["slug"] == "test-hello-world"
    assert len(detail["steps"]) == 1
    assert detail["steps"][0]["step_number"] == 1

    r = await client.post("/api/v1/projects/test-hello-world/start", headers=auth_headers)
    assert r.status_code == 201
    sub = r.json()
    assert sub["current_step"] == 1
    assert sub["completed"] is False

    r = await client.post("/api/v1/projects/test-hello-world/start", headers=auth_headers)
    assert r.status_code == 409

    r = await client.get("/api/v1/projects/test-hello-world/progress", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["current_step"] == 1

    r = await client.post(
        "/api/v1/projects/test-hello-world/submit-step",
        headers=auth_headers,
        json={"step_number": 1, "passed": True},
    )
    assert r.status_code == 200
    result = r.json()
    assert result["completed"] is True

    r = await client.get("/api/v1/projects?track_id=track01")
    assert r.status_code == 200
    assert any(p["slug"] == "test-hello-world" for p in r.json())

    r = await client.get("/api/v1/projects?runtime=python")
    assert r.status_code == 200
    assert any(p["slug"] == "test-hello-world" for p in r.json())
