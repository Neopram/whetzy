"""Instructor marketplace service (Serie 28).

Handles instructor profiles, course management, enrollments, and payouts.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instructor import (
    Instructor,
    InstructorCourse,
    InstructorEnrollment,
    InstructorPayout,
)
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)


class InstructorService:
    """Service for instructor marketplace operations."""

    @staticmethod
    async def get_or_create_instructor(
        db: AsyncSession,
        user_id: str,
        display_name: str,
        bio: str | None = None,
    ) -> Instructor:
        """Get or create instructor profile for a user."""
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
        course_id: str,
        user_id: str,
        gross_payment_cents: int,
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
            gross_payment_cents: Amount student paid (before platform cuts)

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
            raise ValueError(f"Course {course_id} not found")

        # Create enrollment
        enrollment = InstructorEnrollment(
            course_id=course_id,
            user_id=user_id,
        )
        db.add(enrollment)
        await db.flush()  # Flush to get the ID

        # Calculate payout
        payout_calc = PaymentService.calculate_instructor_payout(gross_payment_cents)

        # Create payout record (status='pending' until cron job processes)
        now = datetime.utcnow()
        payout = InstructorPayout(
            instructor_id=course.instructor_id,
            period_start=now.replace(day=1),  # Start of current month
            period_end=now.replace(day=28),   # Approx end (actual: 28-31)
            earnings_cents=payout_calc["instructor_net_cents"],
            status="pending",
        )
        db.add(payout)

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
