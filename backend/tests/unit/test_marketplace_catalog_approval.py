"""28.8: catálogo público del marketplace.

Antes de esto no había manera de ver un curso sin ser el instructor
autenticado -- `GET /instructor/courses` solo lista los cursos propios.
Pieza nueva: `GET /instructor/marketplace/courses`, detrás de
`MARKETPLACE_PUBLIC`, solo cursos `published`.

La aprobación (draft -> published/rejected/archived) ya existía
(`PATCH /admin/instructor/courses/{id}/status`, 28.6) -- el test de punta a
punta de aquí abajo la usa tal cual, sin duplicarla.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.instructor import Instructor, InstructorCourse
from app.models.user import User

CATALOG = "/api/v1/instructor/marketplace/courses"
ADMIN_SET_STATUS = "/api/v1/admin/instructor/courses/{}/status"


def _h(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


async def _course(
    db_session: AsyncSession,
    status: str = "draft",
    price_cents: int = 9900,
    enrolled_count: int = 0,
) -> InstructorCourse:
    tag = uuid.uuid4().hex[:8]
    owner_user = User(
        id=uuid.uuid4(),
        email=f"mkt-owner-{tag}@whetzy.test",
        username=f"mktowner{tag}",
        hashed_password=get_password_hash("Pass123!"),
        display_name="Marketplace Instructor",
        language="es",
    )
    db_session.add(owner_user)
    instructor = Instructor(id=uuid.uuid4(), user_id=owner_user.id, display_name="Catalog Expert")
    db_session.add(instructor)
    course = InstructorCourse(
        id=uuid.uuid4(),
        instructor_id=instructor.id,
        title="Catalog Course",
        price_cents=price_cents,
        status=status,
        enrolled_count=enrolled_count,
    )
    db_session.add(course)
    await db_session.commit()
    return course


@pytest.mark.asyncio
async def test_public_catalog_disabled_by_default_returns_501(client: AsyncClient) -> None:
    assert not settings.MARKETPLACE_PUBLIC, "Precondición: MARKETPLACE_PUBLIC es False por defecto"
    resp = await client.get(CATALOG)
    assert resp.status_code == 501, resp.text


@pytest.mark.asyncio
async def test_public_catalog_lists_published_courses_only(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "MARKETPLACE_PUBLIC", True)
    published = await _course(db_session, status="published", enrolled_count=3)
    await _course(db_session, status="draft")

    resp = await client.get(CATALOG)
    assert resp.status_code == 200, resp.text
    ids = [row["id"] for row in resp.json()]
    assert str(published.id) in ids
    assert len(ids) == 1, "el draft no debe aparecer en el catálogo público"
    row = resp.json()[0]
    assert row["instructor_display_name"] == "Catalog Expert"
    assert "video_url" not in row and "revenue_cents" not in row


@pytest.mark.asyncio
async def test_public_catalog_requires_no_auth(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Es un catálogo público: sin cabecera Authorization también responde."""
    monkeypatch.setattr(settings, "MARKETPLACE_PUBLIC", True)
    resp = await client.get(CATALOG)
    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_an_admin_approved_course_appears_in_the_public_catalog(
    client: AsyncClient, db_session: AsyncSession, owner: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    """De punta a punta: la aprobación de admin ya existente (28.6) hace
    que un draft se vea en el catálogo nuevo de 28.8."""
    monkeypatch.setattr(settings, "MARKETPLACE_PUBLIC", True)
    course = await _course(db_session, status="draft")

    approve_resp = await client.patch(
        ADMIN_SET_STATUS.format(course.id),
        params={"new_status": "published"},
        headers=_h(owner),
    )
    assert approve_resp.status_code == 200, approve_resp.text

    catalog_resp = await client.get(CATALOG)
    assert catalog_resp.status_code == 200, catalog_resp.text
    assert str(course.id) in [row["id"] for row in catalog_resp.json()]
