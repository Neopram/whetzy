"""B1: direct enrollment is blocked when the payment gateway is not configured.

POST /instructor/courses/{id}/enroll must return 501 (Not Implemented) when
INSTRUCTOR_MARKETPLACE_ENABLED is False (the default) so that users cannot
obtain a free enrollment by calling the API directly before Paddle is live.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.instructor import Instructor, InstructorCourse
from app.models.user import User

ENROLL = "/api/v1/instructor/courses/{}/enroll"


async def _published_course(db_session: AsyncSession, price_cents: int = 9900) -> InstructorCourse:
    tag = uuid.uuid4().hex[:8]
    owner = User(
        id=uuid.uuid4(),
        email=f"b1-owner-{tag}@whetzy.test",
        username=f"b1owner{tag}",
        hashed_password=get_password_hash("Pass123!"),
        display_name="B1 Instructor",
        language="es",
    )
    db_session.add(owner)
    instructor = Instructor(id=uuid.uuid4(), user_id=owner.id, display_name="B1 Expert")
    db_session.add(instructor)
    course = InstructorCourse(
        id=uuid.uuid4(),
        instructor_id=instructor.id,
        title="Paid Course" if price_cents else "Free Course",
        price_cents=price_cents,
        status="published",
    )
    db_session.add(course)
    await db_session.commit()
    return course


@pytest.mark.asyncio
async def test_direct_enroll_returns_501_without_payment_gateway(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
) -> None:
    """Enrollment endpoint must be disabled (501) until Paddle is live (B1)."""
    assert not settings.INSTRUCTOR_MARKETPLACE_ENABLED, (
        "Test pre-condition: INSTRUCTOR_MARKETPLACE_ENABLED must be False by default"
    )
    course = await _published_course(db_session)
    response = await client.post(ENROLL.format(course.id), headers=auth_headers)
    assert response.status_code == 501, response.text


@pytest.mark.asyncio
async def test_enroll_enabled_via_flag_returns_201_for_a_free_course(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With the flag enabled the endpoint works (regression guard for the logic)."""
    monkeypatch.setattr(settings, "INSTRUCTOR_MARKETPLACE_ENABLED", True)
    course = await _published_course(db_session, price_cents=0)
    response = await client.post(ENROLL.format(course.id), headers=auth_headers)
    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_enroll_enabled_via_flag_still_needs_payment_for_a_paid_course(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Encender el marketplace no abre los cursos de pago sin cobro (41.6, #166)."""
    monkeypatch.setattr(settings, "INSTRUCTOR_MARKETPLACE_ENABLED", True)
    course = await _published_course(db_session)
    response = await client.post(ENROLL.format(course.id), headers=auth_headers)
    assert response.status_code == 402, response.text
