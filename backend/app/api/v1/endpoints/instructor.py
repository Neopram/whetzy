"""Instructor marketplace endpoints: profiles, courses, enrollments, analytics (28.0)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User

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
    price_cents: int = Field(..., ge=0)  # cents; >= 0
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


class AnalyticsResponse(BaseModel):
    """Instructor analytics dashboard."""

    total_earnings_cents: int
    total_revenue_cents: int  # before platform split
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
    """Get public instructor profile.

    **Status**: 28.0 Scaffold (stub, returns mock data)
    """
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
    """Upload new course.

    **Requires**: Instructor role.
    **Status**: 28.0 Scaffold (stub, returns 501 NotImplemented for now)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Course upload endpoints pending 28.1 implementation"
    )


@router.get("/courses", response_model=list[CourseResponse])
async def list_courses(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CourseResponse]:
    """List instructor's courses.

    **Status**: 28.0 Scaffold (returns mock data)
    """
    return [
        CourseResponse(
            id="course-1",
            title="Python Basics",
            description="Learn Python fundamentals",
            price_cents=9999,
            video_url=None,
            materials_url=None,
            enrolled_count=42,
            revenue_cents=629930,  # 42 * 9999 * 0.70 ≈ 629930 cents
            status="published",
            created_at="2026-09-01T00:00:00Z"
        )
    ]


# ============================================================================
# Analytics Endpoints
# ============================================================================


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalyticsResponse:
    """Get instructor analytics dashboard.

    **Requires**: Instructor role.
    **Status**: 28.0 Scaffold (returns mock data)
    """
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
    """Get payout history.

    **Status**: 28.0 Scaffold (stub, depends on H.29 payout rail decision)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Payout endpoints pending H.29 payment rail integration"
    )
