"""Instructor marketplace endpoints: courses, enrollments, analytics (Serie 28).

Endpoints:
- POST   /instructor/courses              Create course
- GET    /instructor/courses              List courses
- POST   /instructor/courses/{id}/enroll  Enroll student (triggers payout calc)
- GET    /instructor/analytics            Earnings dashboard
- GET    /instructor/payouts              Payout history
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.entitlements import user_meets_tier
from app.core.security import get_current_user
from app.models.instructor import Instructor, InstructorCourse
from app.models.user import User
from app.services.instructor_service import (
    AlreadyEnrolled,
    CourseNotPublished,
    InstructorService,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class CourseCreateRequest(BaseModel):
    """Create new instructor course."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price_cents: int = Field(..., ge=1)
    video_url: str | None = None
    materials_url: str | None = None


class CourseResponse(BaseModel):
    """Instructor course response."""
    id: str
    instructor_id: str
    title: str
    description: str | None
    price_cents: int
    video_url: str | None
    materials_url: str | None
    enrolled_count: int
    revenue_cents: int
    status: str
    created_at: str


class EnrollmentResponse(BaseModel):
    """Enrollment confirmation with payout details."""
    enrollment_id: str
    payout_id: str
    instructor_id: str
    gross_cents: int
    paddle_commission_cents: int
    instructor_gross_cents: int
    tax_withheld_cents: int
    instructor_net_cents: int
    status: str


class AnalyticsResponse(BaseModel):
    """Instructor analytics dashboard."""
    total_earnings_cents: int
    pending_payout_cents: int
    active_courses: int
    total_students: int
    avg_completion_percent: float


class PayoutResponse(BaseModel):
    """Payout history entry."""
    id: str
    period_start: str
    period_end: str
    earnings_cents: int
    status: str
    payout_date: str | None


async def _current_instructor(db: AsyncSession, user: User) -> Instructor:
    """Perfil de instructor del usuario autenticado, creandolo si hace falta.

    El marketplace no tiene alta aparte: publicar un curso te convierte en
    instructor. `display_name` sale del perfil del usuario para no pedir dos
    veces lo mismo.
    """
    return await InstructorService.get_or_create_instructor(
        db,
        user_id=user.id,
        display_name=user.display_name or user.username,
    )


def _course_payload(course: InstructorCourse) -> CourseResponse:
    return CourseResponse(
        id=str(course.id),
        instructor_id=str(course.instructor_id),
        title=course.title,
        description=course.description,
        price_cents=int(course.price_cents),
        video_url=course.video_url,
        materials_url=course.materials_url,
        enrolled_count=int(course.enrolled_count or 0),
        revenue_cents=int(course.revenue_cents or 0),
        status=course.status,
        created_at=course.created_at.isoformat(),
    )


@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    body: CourseCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CourseResponse:
    """Publica un curso nuevo del instructor autenticado.

    Con ``CREATOR_PLAN_REQUIRED`` exige el plan Creador (ADR-45); el dueño y
    los admins quedan fuera de la regla para poder montar el catálogo propio.
    """
    if (
        settings.CREATOR_PLAN_REQUIRED
        and not user_meets_tier(user, "creator")
        and not (user.is_admin or user.role == "owner")
    ):
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="creator_plan_required")
    instructor = await _current_instructor(db, user)
    course = InstructorCourse(
        instructor_id=instructor.id,
        title=body.title,
        description=body.description,
        price_cents=body.price_cents,
        video_url=body.video_url,
        materials_url=body.materials_url,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return _course_payload(course)


@router.get("/courses", response_model=list[CourseResponse])
async def list_courses(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CourseResponse]:
    """Cursos del instructor autenticado, el mas reciente primero."""
    instructor = await _current_instructor(db, user)
    courses = await db.scalars(
        select(InstructorCourse)
        .where(InstructorCourse.instructor_id == instructor.id)
        .order_by(InstructorCourse.created_at.desc())
    )
    return [_course_payload(c) for c in courses]


@router.post(
    "/courses/{course_id}/enroll",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_student(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EnrollmentResponse:
    """Inscribe al usuario y acumula el reparto en el pago del mes (28.4-28.6).

    El desglose que devuelve es el de `PaymentService`: comision de Paddle,
    80/20 (ADR-45) y retencion, con los parametros que fijo H.29. El importe es el
    precio del curso; no se acepta en la peticion.

    Sin pasarela todavia (Paddle es HUMAN-BLOCKED), esto registra la
    inscripcion y el reparto pero no cobra: no exponer en la UI como compra
    hasta que el webhook de Paddle sea quien lo llame.
    """
    # La columna es UUID; con el id como texto SQLAlchemy revienta antes de
    # llegar a la consulta, y eso convertia cualquier inscripcion en un 500.
    try:
        course_uuid = uuid.UUID(course_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found") from exc
    try:
        result = await InstructorService.enroll_student_in_course(
            db, course_id=course_uuid, user_id=user.id
        )
    except AlreadyEnrolled as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except CourseNotPublished as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return EnrollmentResponse(**result)


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalyticsResponse:
    """Ingresos, pagos pendientes y alumnos del instructor autenticado."""
    instructor = await _current_instructor(db, user)
    data = await InstructorService.get_instructor_analytics(db, str(instructor.id))
    return AnalyticsResponse(**data)


@router.get("/payouts", response_model=list[PayoutResponse])
async def get_payout_history(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[PayoutResponse]:
    """Historico de pagos del instructor, ultimos 12 periodos."""
    instructor = await _current_instructor(db, user)
    rows = await InstructorService.get_payout_history(db, str(instructor.id))
    return [PayoutResponse(**r) for r in rows]
