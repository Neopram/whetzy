"""Inscripción en cursos de instructor (28.4-28.6).

El alumno es el usuario autenticado y el importe es el precio del curso. La
versión anterior de estos tests enviaba `student_id` en el body y el endpoint
aceptaba `gross_payment_cents` del cliente: ninguno de los dos contratos era
el bueno.
"""

import uuid

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.instructor import (
    Instructor,
    InstructorCourse,
    InstructorEnrollment,
    InstructorPayout,
)
from app.models.user import User

ENROLL = "/api/v1/instructor/courses/{}/enroll"


# B1: enable the marketplace gate for all tests in this file — they test the
# enrollment logic, not the payment-gateway guard (which has its own test).
@pytest.fixture(autouse=True)
def _enable_marketplace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "INSTRUCTOR_MARKETPLACE_ENABLED", True)


async def _course(db_session, *, price_cents: int, status: str = "published") -> InstructorCourse:
    tag = uuid.uuid4().hex[:8]
    owner = User(
        id=uuid.uuid4(),
        email=f"instructor-{tag}@whetzy.test",
        username=f"instr{tag}",
        hashed_password=get_password_hash("Pass123!"),
        display_name="Instructor",
        language="es",
    )
    db_session.add(owner)
    instructor = Instructor(id=uuid.uuid4(), user_id=owner.id, display_name="Expert Instructor")
    db_session.add(instructor)
    course = InstructorCourse(
        id=uuid.uuid4(),
        instructor_id=instructor.id,
        title="Advanced Python",
        price_cents=price_cents,
        status=status,
    )
    db_session.add(course)
    await db_session.commit()
    return course


@pytest.mark.asyncio
async def test_enroll_in_published_course_creates_payout(client, db_session, auth_headers, user):
    course = await _course(db_session, price_cents=10000)

    response = await client.post(ENROLL.format(course.id), headers=auth_headers)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["instructor_id"] == str(course.instructor_id)
    assert data["gross_cents"] == 10000
    # 10000 - 7.5 % Paddle = 9250; 80 % = 7400; - 22 % retencion = 5772 (H.29, ADR-41)
    assert data["instructor_net_cents"] == 5772
    assert data["status"] == "pending"

    enrollment = await db_session.scalar(
        select(InstructorEnrollment).where(
            InstructorEnrollment.course_id == course.id,
            InstructorEnrollment.user_id == user.id,
        )
    )
    assert enrollment is not None
    assert enrollment.progress_percent == 0

    payout = await db_session.scalar(
        select(InstructorPayout).where(InstructorPayout.id == uuid.UUID(data["payout_id"]))
    )
    assert payout is not None
    assert payout.instructor_id == course.instructor_id
    assert payout.status == "pending"
    assert payout.earnings_cents == 5772


@pytest.mark.asyncio
async def test_enroll_ignores_a_price_sent_by_the_client(client, db_session, auth_headers):
    """El agujero original: el cliente decía cuánto había pagado."""
    course = await _course(db_session, price_cents=10000)

    response = await client.post(
        ENROLL.format(course.id), json={"gross_payment_cents": 1}, headers=auth_headers
    )

    assert response.status_code == 201, response.text
    assert response.json()["gross_cents"] == 10000


@pytest.mark.asyncio
async def test_enroll_duplicate_enrollment_fails(client, db_session, auth_headers, user):
    course = await _course(db_session, price_cents=5000)
    db_session.add(InstructorEnrollment(course_id=course.id, user_id=user.id))
    await db_session.commit()

    response = await client.post(ENROLL.format(course.id), headers=auth_headers)

    assert response.status_code == 409
    assert "already enrolled" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_enroll_unpublished_course_fails(client, db_session, auth_headers):
    course = await _course(db_session, price_cents=15000, status="draft")

    response = await client.post(ENROLL.format(course.id), headers=auth_headers)

    assert response.status_code == 403
    assert "draft" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_enroll_unknown_course_is_404(client, auth_headers):
    response = await client.post(ENROLL.format(uuid.uuid4()), headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_instructor_cannot_enroll_in_their_own_course(client, db_session, auth_headers, user):
    """Sin pasarela, inscribirse no cobra pero sí genera un InstructorPayout
    real — sin este chequeo, el propio instructor podía "venderse" su curso."""
    instructor = Instructor(id=uuid.uuid4(), user_id=user.id, display_name=user.display_name)
    db_session.add(instructor)
    course = InstructorCourse(
        id=uuid.uuid4(),
        instructor_id=instructor.id,
        title="My Own Course",
        price_cents=10000,
        status="published",
    )
    db_session.add(course)
    await db_session.commit()

    response = await client.post(ENROLL.format(course.id), headers=auth_headers)

    assert response.status_code == 403
    assert "own course" in response.json()["detail"].lower()

    enrollment = await db_session.scalar(
        select(InstructorEnrollment).where(
            InstructorEnrollment.course_id == course.id,
            InstructorEnrollment.user_id == user.id,
        )
    )
    assert enrollment is None

    payout = await db_session.scalar(
        select(InstructorPayout).where(InstructorPayout.instructor_id == instructor.id)
    )
    assert payout is None
