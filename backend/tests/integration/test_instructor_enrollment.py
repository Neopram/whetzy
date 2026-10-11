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
async def test_enroll_in_a_paid_course_without_a_confirmed_purchase_is_blocked(
    client, db_session, auth_headers, user
):
    """41.6: antes de esto, inscribirse en un curso de pago no cobraba nada y
    aun así sumaba `price_cents` a `revenue_cents` y creaba un `InstructorPayout`
    real — dinero que se le debería al instructor por una venta que nunca
    existió. No hay ningún producto Paddle de curso todavía (`webhooks.py` solo
    liga `transaction.completed` a certificaciones), así que no hay manera de
    confirmar el cobro: toca bloquear, no fabricar la fila."""
    course = await _course(db_session, price_cents=10000)

    response = await client.post(ENROLL.format(course.id), headers=auth_headers)

    assert response.status_code == 402, response.text

    enrollment = await db_session.scalar(
        select(InstructorEnrollment).where(
            InstructorEnrollment.course_id == course.id,
            InstructorEnrollment.user_id == user.id,
        )
    )
    assert enrollment is None

    payout = await db_session.scalar(
        select(InstructorPayout).where(InstructorPayout.instructor_id == course.instructor_id)
    )
    assert payout is None

    course_after = await db_session.get(InstructorCourse, course.id)
    assert course_after.revenue_cents == 0


@pytest.mark.asyncio
async def test_enroll_ignores_a_price_sent_by_the_client(client, db_session, auth_headers):
    """El agujero original: el cliente decía cuánto había pagado. Hoy ningún
    curso de pago se puede comprar sin una pasarela (41.6), así que una
    petición con un precio inventado también cae en el mismo 402."""
    course = await _course(db_session, price_cents=10000)

    response = await client.post(
        ENROLL.format(course.id), json={"gross_payment_cents": 1}, headers=auth_headers
    )

    assert response.status_code == 402, response.text


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
