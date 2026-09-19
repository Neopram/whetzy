"""Instructor marketplace endpoints: profiles, courses, enrollments, analytics (28.0+)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.instructor import (
    Instructor, InstructorCourse, InstructorEnrollment, InstructorPayout
)
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Request/Response Models (Pydantic schemas)
# ============================================================================


class InstructorProfileRequest(BaseModel):
    """Create/update instructor profile."""

    display_name: str = Field(..., min_length=1, max_length=100)
    bio: str | None = None
    avatar_url: str | None = None
    website: str | None = None


class InstructorProfileResponse(BaseModel):
    """Instructor profile response."""

    id: str
    user_id: str
    display_name: str
    bio: str | None
    avatar_url: str | None
    website: str | None
    verified_at: str | None
    created_at: str


class CourseUploadRequest(BaseModel):
    """Upload new course."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price_cents: int = Field(..., ge=0)
    video_url: str | None = None
    materials_url: str | None = None


class CourseResponse(BaseModel):
    """Instructor course response."""

    id: str
    title: str
    description: str | None
    price_cents: int
    video_url: str | None
    materials_url: str | None
    enrolled_count: int
    revenue_cents: int
    status: str
    created_at: str


class EnrollmentRequest(BaseModel):
    """Student enrollment request for instructor course."""
    
    student_id: str = Field(..., description="UUID of the student enrolling")


class EnrollmentResponse(BaseModel):
    """Enrollment and payout response."""
    
    course_id: str
    instructor_id: str
    payout_id: str
    student_id: str
    gross_cents: int
    instructor_net_cents: int
    status: str = "pending"


class AnalyticsResponse(BaseModel):
    """Instructor analytics dashboard."""

    total_earnings_cents: int
    total_revenue_cents: int
    active_courses: int
    total_students: int
    avg_completion_percent: float
    pending_payout_cents: int


class PayoutHistoryResponse(BaseModel):
    """Payout history entry."""

    id: str
    period_start: str
    period_end: str
    earnings_cents: int
    status: str
    payout_date: str | None


# ============================================================================
# Profile Endpoints
# ============================================================================


@router.post("/profile", response_model=InstructorProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_profile(
    body: InstructorProfileRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InstructorProfileResponse:
    """Create or update instructor profile.

    **Status**: 28.0 Scaffold (stub, returns 501 NotImplemented for now)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Instructor profile endpoints pending 28.1 implementation"
    )


@router.get("/profile/{instructor_id}", response_model=InstructorProfileResponse)
async def get_profile(
    instructor_id: str,
    db: AsyncSession = Depends(get_db),
) -> InstructorProfileResponse:
    """Get public instructor profile."""
    return InstructorProfileResponse(
        id=instructor_id,
        user_id="mock-user-id",
        display_name="Mock Instructor",
        bio="This is a mock instructor profile.",
        avatar_url=None,
        website=None,
        verified_at=None,
        created_at="2026-09-19T00:00:00Z"
    )


# ============================================================================
# Course Endpoints
# ============================================================================


@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def upload_course(
    body: CourseUploadRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CourseResponse:
    """Upload new course."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Course upload endpoints pending 28.1 implementation"
    )


@router.get("/courses", response_model=list[CourseResponse])
async def list_courses(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CourseResponse]:
    """List instructor's courses."""
    return [
        CourseResponse(
            id="course-1",
            title="Python Basics",
            description="Learn Python fundamentals",
            price_cents=9999,
            video_url=None,
            materials_url=None,
            enrolled_count=42,
            revenue_cents=629930,
            status="published",
            created_at="2026-09-01T00:00:00Z"
        )
    ]


# ============================================================================
# Enrollment Endpoints (28.4-28.6: Payment split 70/30)
# ============================================================================


@router.post(
    "/courses/{course_id}/enroll",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["enrollment"],
)
async def enroll_in_course(
    course_id: str,
    body: EnrollmentRequest,
    db: AsyncSession = Depends(get_db),
) -> EnrollmentResponse:
    """Enroll a student in an instructor course and create payout record (28.4-28.6)."""
    try:
        student_id_uuid = uuid.UUID(body.student_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student_id format (must be UUID)"
        )
    
    try:
        course_id_uuid = uuid.UUID(course_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course_id format (must be UUID)"
        )
    
    stmt = select(InstructorCourse).where(InstructorCourse.id == course_id_uuid)
    result = await db.execute(stmt)
    course = result.scalars().first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_id} not found"
        )
    
    if course.status != "published":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Course status is '{course.status}', must be 'published'"
        )
    
    stmt = select(InstructorEnrollment).where(
        (InstructorEnrollment.course_id == course_id_uuid) &
        (InstructorEnrollment.user_id == student_id_uuid)
    )
    result = await db.execute(stmt)
    existing = result.scalars().first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student {body.student_id} is already enrolled in this course"
        )
    
    enrollment = InstructorEnrollment(
        course_id=course_id_uuid,
        user_id=student_id_uuid,
        progress_percent=0,
    )
    db.add(enrollment)
    
    payout_calc = PaymentService.calculate_instructor_payout(course.price_cents)
    
    logger.info(
        f"Enrollment created | course_id={course_id} student_id={body.student_id} "
        f"instructor_id={course.instructor_id} payout_calc={payout_calc}"
    )
    
    now = datetime.utcnow()
    payout = InstructorPayout(
        instructor_id=course.instructor_id,
        period_start=datetime(now.year, now.month, 1),
        period_end=datetime(now.year, now.month, 28),
        earnings_cents=payout_calc["instructor_net_cents"],
        status="pending",
    )
    db.add(payout)
    
    await db.commit()
    await db.refresh(enrollment)
    await db.refresh(payout)
    
    logger.info(
        f"InstructorPayout created | payout_id={payout.id} instructor_id={course.instructor_id} "
        f"gross_cents={payout_calc['gross_cents']} instructor_net_cents={payout_calc['instructor_net_cents']}"
    )
    
    return EnrollmentResponse(
        course_id=str(course_id_uuid),
        instructor_id=str(course.instructor_id),
        payout_id=str(payout.id),
        student_id=str(student_id_uuid),
        gross_cents=payout_calc["gross_cents"],
        instructor_net_cents=payout_calc["instructor_net_cents"],
        status="pending",
    )


# ============================================================================
# Analytics Endpoints
# ============================================================================


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalyticsResponse:
    """Get instructor analytics dashboard."""
    return AnalyticsResponse(
        total_earnings_cents=629930,
        total_revenue_cents=899900,
        active_courses=1,
        total_students=42,
        avg_completion_percent=65.5,
        pending_payout_cents=629930
    )


# ============================================================================
# Payout Endpoints (Stub)
# ============================================================================


@router.get("/payouts", response_model=list[PayoutHistoryResponse])
async def get_payout_history(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[PayoutHistoryResponse]:
    """Get payout history."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Payout endpoints pending H.29 payment rail integration"
    )
