"""Instructor marketplace service (Serie 28).

Handles instructor profiles, course management, enrollments, and payouts.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instructor import (
    Instructor,
    InstructorCourse,
    InstructorEnrollment,
    InstructorPayout,
)
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)


class CourseNotFound(ValueError):
    pass


class CourseNotPublished(ValueError):
    """El curso existe pero no está a la venta (draft, archived...)."""


class AlreadyEnrolled(ValueError):
    """El alumno ya está inscrito; sin esto la unique constraint daba un 500."""


class InstructorService:
    """Service for instructor marketplace operations."""

    @staticmethod
    async def get_or_create_instructor(
        db: AsyncSession,
        user_id: uuid.UUID | str,
        display_name: str,
        bio: str | None = None,
    ) -> Instructor:
        """Get or create instructor profile for a user.

        El id se normaliza a `UUID`: con texto, Postgres lo aceptaba pero SQLite
        (la base de los tests) fallaba con «'str' object has no attribute
        'hex'», así que `POST /instructor/courses` no tenía ningún test.
        """
        user_id = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(user_id)
        stmt = select(Instructor).where(Instructor.user_id == user_id)
        result = await db.execute(stmt)
        instructor = result.scalars().first()

        if instructor:
            return instructor

        instructor = Instructor(
            user_id=user_id,
            display_name=display_name,
            bio=bio,
        )
        db.add(instructor)
        await db.commit()
        await db.refresh(instructor)
        return instructor

    @staticmethod
    async def enroll_student_in_course(
        db: AsyncSession,
        course_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Enroll student in course and calculate instructor payout.

        Serie 28.4-28.6: When student buys a course:
        1. Create InstructorEnrollment record
        2. Calculate payout using PaymentService
        3. Create InstructorPayout (status='pending')
        4. Return enrollment + payout details

        Args:
            db: Database session
            course_id: UUID of course
            user_id: UUID of student

        El importe es `course.price_cents`. Antes venía en la petición y
        cualquiera podía comprar un curso de 100 EUR enviando 1.

        Returns:
            {
                'enrollment_id': str,
                'payout_id': str,
                'instructor_id': str,
                'gross_cents': int,
                'instructor_net_cents': int,
                'status': 'pending'
            }
        """
        # Get course and instructor
        stmt_course = select(InstructorCourse).where(InstructorCourse.id == course_id)
        result = await db.execute(stmt_course)
        course = result.scalars().first()

        if not course:
            raise CourseNotFound(f"Course {course_id} not found")
        if course.status != "published":
            raise CourseNotPublished(f"Course {course_id} is {course.status}, not published")

        already = await db.scalar(
            select(InstructorEnrollment.id).where(
                InstructorEnrollment.course_id == course_id,
                InstructorEnrollment.user_id == user_id,
            )
        )
        if already is not None:
            raise AlreadyEnrolled(f"User {user_id} is already enrolled in course {course_id}")

        gross_payment_cents = int(course.price_cents)

        # Create enrollment
        enrollment = InstructorEnrollment(
            course_id=course_id,
            user_id=user_id,
        )
        db.add(enrollment)
        await db.flush()  # Flush to get the ID

        # Calculate payout
        payout_calc = PaymentService.calculate_instructor_payout(gross_payment_cents)

        # Un pago por instructor y mes, no uno por inscripcion. Con una fila
        # por alumno, un curso con 50 ventas generaba 50 pagos sueltos y el
        # minimo de 50 EUR del job los descartaba casi todos uno a uno, aunque
        # la suma pasara de sobra.
        now = datetime.now(UTC)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (period_start + timedelta(days=32)).replace(day=1)
        period_end = next_month - timedelta(microseconds=1)

        payout = await db.scalar(
            select(InstructorPayout).where(
                InstructorPayout.instructor_id == course.instructor_id,
                InstructorPayout.period_start == period_start,
                InstructorPayout.status == "pending",
            )
        )
        if payout is None:
            payout = InstructorPayout(
                instructor_id=course.instructor_id,
                period_start=period_start,
                period_end=period_end,
                earnings_cents=payout_calc["instructor_net_cents"],
                status="pending",
            )
            db.add(payout)
        else:
            payout.earnings_cents = (
                int(payout.earnings_cents) + payout_calc["instructor_net_cents"]
            )

        # Update course stats
        course.enrolled_count = (course.enrolled_count or 0) + 1
        course.revenue_cents = (course.revenue_cents or 0) + gross_payment_cents

        await db.commit()
        await db.refresh(enrollment)
        await db.refresh(payout)

        return {
            "enrollment_id": str(enrollment.id),
            "payout_id": str(payout.id),
            "instructor_id": str(course.instructor_id),
            "gross_cents": payout_calc["gross_cents"],
            "paddle_commission_cents": payout_calc["paddle_commission_cents"],
            "instructor_gross_cents": payout_calc["instructor_gross_cents"],
            "tax_withheld_cents": payout_calc["tax_withheld_cents"],
            "instructor_net_cents": payout_calc["instructor_net_cents"],
            "status": "pending",
        }

    @staticmethod
    async def get_instructor_analytics(
        db: AsyncSession,
        instructor_id: str,
    ) -> dict[str, Any]:
        """Get instructor analytics dashboard (earnings, payouts, students)."""
        # Total earnings (sum of all completed payouts)
        stmt_completed = (
            select(func.sum(InstructorPayout.earnings_cents))
            .where(InstructorPayout.instructor_id == instructor_id)
            .where(InstructorPayout.status == "completed")
        )
        result = await db.execute(stmt_completed)
        completed_earnings_cents = result.scalar() or 0

        # Pending payouts
        stmt_pending = (
            select(func.sum(InstructorPayout.earnings_cents))
            .where(InstructorPayout.instructor_id == instructor_id)
            .where(InstructorPayout.status == "pending")
        )
        result = await db.execute(stmt_pending)
        pending_payout_cents = result.scalar() or 0

        # Active courses
        stmt_courses = (
            select(func.count(InstructorCourse.id))
            .where(InstructorCourse.instructor_id == instructor_id)
            .where(InstructorCourse.status == "published")
        )
        result = await db.execute(stmt_courses)
        active_courses = result.scalar() or 0

        # Total students (unique enrollments)
        stmt_students = (
            select(func.count(func.distinct(InstructorEnrollment.user_id)))
            .join(InstructorCourse)
            .where(InstructorCourse.instructor_id == instructor_id)
        )
        result = await db.execute(stmt_students)
        total_students = result.scalar() or 0

        # Average completion
        stmt_completion = (
            select(func.avg(InstructorEnrollment.progress_percent))
            .join(InstructorCourse)
            .where(InstructorCourse.instructor_id == instructor_id)
        )
        result = await db.execute(stmt_completion)
        avg_completion = result.scalar() or 0.0

        return {
            "total_earnings_cents": int(completed_earnings_cents),
            "pending_payout_cents": int(pending_payout_cents),
            "active_courses": active_courses,
            "total_students": total_students,
            "avg_completion_percent": float(avg_completion),
        }

    @staticmethod
    async def get_payout_history(
        db: AsyncSession,
        instructor_id: str,
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        """Get instructor payout history (last N months)."""
        stmt = (
            select(InstructorPayout)
            .where(InstructorPayout.instructor_id == instructor_id)
            .order_by(InstructorPayout.period_start.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        payouts = result.scalars().all()

        return [
            {
                "id": str(p.id),
                "period_start": p.period_start.isoformat(),
                "period_end": p.period_end.isoformat(),
                "earnings_cents": int(p.earnings_cents),
                "status": p.status,
                "payout_date": p.payout_date.isoformat() if p.payout_date else None,
            }
            for p in payouts
        ]
