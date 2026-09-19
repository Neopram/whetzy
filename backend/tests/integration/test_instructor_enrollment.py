"""Integration test for instructor enrollment endpoint (Series 28.4-28.6)."""

import pytest
import uuid
from datetime import datetime
from sqlalchemy import select

from app.models.instructor import Instructor, InstructorCourse, InstructorEnrollment, InstructorPayout
from app.models.user import User
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_enroll_in_published_course_creates_payout(client, db_session, auth_headers):
    """E2E test: POST /instructor/courses/{course_id}/enroll creates enrollment + payout."""
    
    # Setup: Create instructor and student users
    instructor_user = User(
        id=uuid.uuid4(),
        email="instructor@test.com",
        username="instructor1",
        hashed_password=get_password_hash("Pass123!"),
        display_name="Instructor",
        language="es",
    )
    
    student_user = User(
        id=uuid.uuid4(),
        email="student@test.com",
        username="student1",
        hashed_password=get_password_hash("Pass123!"),
        display_name="Student",
        language="es",
    )
    
    db_session.add(instructor_user)
    db_session.add(student_user)
    
    # Create instructor profile
    instructor = Instructor(
        id=uuid.uuid4(),
        user_id=instructor_user.id,
        display_name="Expert Instructor",
    )
    db_session.add(instructor)
    
    # Create published course with EUR 100 price (10000 cents)
    course = InstructorCourse(
        id=uuid.uuid4(),
        instructor_id=instructor.id,
        title="Advanced Python",
        price_cents=10000,
        status="published",
    )
    db_session.add(course)
    
    await db_session.commit()
    
    # Test: POST /instructor/courses/{course_id}/enroll
    response = await client.post(
        f"/api/v1/instructor/courses/{course.id}/enroll",
        json={"student_id": str(student_user.id)},
        headers=auth_headers,
    )
    
    # Verify response
    assert response.status_code == 201
    data = response.json()
    
    assert data["course_id"] == str(course.id)
    assert data["instructor_id"] == str(instructor.id)
    assert data["student_id"] == str(student_user.id)
    assert data["gross_cents"] == 10000
    assert data["instructor_net_cents"] == 5050  # After 70/30 split + tax
    assert data["status"] == "pending"
    
    # Verify: InstructorEnrollment created in DB
    stmt = select(InstructorEnrollment).where(
        (InstructorEnrollment.course_id == course.id) &
        (InstructorEnrollment.user_id == student_user.id)
    )
    result = await db_session.execute(stmt)
    enrollment = result.scalars().first()
    
    assert enrollment is not None
    assert enrollment.progress_percent == 0
    
    # Verify: InstructorPayout created with status=pending
    payout_id = uuid.UUID(data["payout_id"])
    stmt = select(InstructorPayout).where(InstructorPayout.id == payout_id)
    result = await db_session.execute(stmt)
    payout = result.scalars().first()
    
    assert payout is not None
    assert payout.instructor_id == instructor.id
    assert payout.status == "pending"
    assert payout.earnings_cents == 5050


@pytest.mark.asyncio
async def test_enroll_duplicate_enrollment_fails(client, db_session, auth_headers):
    """Test: Duplicate enrollment returns 409 Conflict."""
    
    # Setup
    instructor_user = User(
        id=uuid.uuid4(),
        email="instructor2@test.com",
        username="instructor2",
        hashed_password=get_password_hash("Pass123!"),
        display_name="Instructor 2",
        language="es",
    )
    
    student_user = User(
        id=uuid.uuid4(),
        email="student2@test.com",
        username="student2",
        hashed_password=get_password_hash("Pass123!"),
        display_name="Student 2",
        language="es",
    )
    
    db_session.add(instructor_user)
    db_session.add(student_user)
    
    instructor = Instructor(
        id=uuid.uuid4(),
        user_id=instructor_user.id,
        display_name="Instructor 2",
    )
    db_session.add(instructor)
    
    course = InstructorCourse(
        id=uuid.uuid4(),
        instructor_id=instructor.id,
        title="Python Basics",
        price_cents=5000,
        status="published",
    )
    db_session.add(course)
    
    # First enrollment
    enrollment = InstructorEnrollment(
        course_id=course.id,
        user_id=student_user.id,
    )
    db_session.add(enrollment)
    
    await db_session.commit()
    
    # Test: Second enrollment attempt
    response = await client.post(
        f"/api/v1/instructor/courses/{course.id}/enroll",
        json={"student_id": str(student_user.id)},
        headers=auth_headers,
    )
    
    assert response.status_code == 409  # Conflict
    assert "already enrolled" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_enroll_unpublished_course_fails(client, db_session, auth_headers):
    """Test: Enrolling in unpublished course returns 403 Forbidden."""
    
    # Setup
    instructor_user = User(
        id=uuid.uuid4(),
        email="instructor3@test.com",
        username="instructor3",
        hashed_password=get_password_hash("Pass123!"),
        display_name="Instructor 3",
        language="es",
    )
    
    student_user = User(
        id=uuid.uuid4(),
        email="student3@test.com",
        username="student3",
        hashed_password=get_password_hash("Pass123!"),
        display_name="Student 3",
        language="es",
    )
    
    db_session.add(instructor_user)
    db_session.add(student_user)
    
    instructor = Instructor(
        id=uuid.uuid4(),
        user_id=instructor_user.id,
        display_name="Instructor 3",
    )
    db_session.add(instructor)
    
    course = InstructorCourse(
        id=uuid.uuid4(),
        instructor_id=instructor.id,
        title="Draft Course",
        price_cents=15000,
        status="draft",  # Not published
    )
    db_session.add(course)
    
    await db_session.commit()
    
    # Test
    response = await client.post(
        f"/api/v1/instructor/courses/{course.id}/enroll",
        json={"student_id": str(student_user.id)},
        headers=auth_headers,
    )
    
    assert response.status_code == 403
    assert "draft" in response.json()["detail"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
