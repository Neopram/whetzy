"""Integration test — tutor personalizes explanation by times_missed.

Tests `_times_missed()` directly against a live SQLite session so there is
no FastAPI app import (avoids the module-level engine-creation order issue).
Verifies: count goes from 0 → 1 → 2 as wrong responses are inserted.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.session import Response, StudySession
from app.services.ai.tutor import _times_missed

DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def db_session():
    engine = create_async_engine(DB_URL, echo=False)
    async with engine.begin() as conn:
        # Only create the tables we need for this test
        await conn.run_sync(
            lambda c: (
                c.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        username TEXT,
                        email TEXT,
                        hashed_password TEXT,
                        language TEXT DEFAULT 'es',
                        level INTEGER DEFAULT 1,
                        xp INTEGER DEFAULT 0,
                        streak_days INTEGER DEFAULT 0,
                        last_active_date TEXT,
                        created_at TEXT,
                        league_id TEXT,
                        refresh_token TEXT
                    )
                """)),
                c.execute(text("""
                    CREATE TABLE IF NOT EXISTS study_sessions (
                        id TEXT PRIMARY KEY,
                        user_id TEXT,
                        mode TEXT DEFAULT 'study',
                        started_at TEXT,
                        ended_at TEXT,
                        questions_answered INTEGER DEFAULT 0,
                        correct_count INTEGER DEFAULT 0,
                        xp_earned INTEGER DEFAULT 0,
                        max_combo INTEGER DEFAULT 0
                    )
                """)),
                c.execute(text("""
                    CREATE TABLE IF NOT EXISTS responses (
                        id TEXT PRIMARY KEY,
                        session_id TEXT,
                        question_id TEXT,
                        correct INTEGER,
                        grade INTEGER DEFAULT 0,
                        response_time_ms INTEGER DEFAULT 0,
                        created_at TEXT,
                        question_version INTEGER DEFAULT 1
                    )
                """)),
            )
        )
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


def _uid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.mark.asyncio
async def test_times_missed_zero_initially(db_session: AsyncSession):
    user_id = _uid()
    q_id = "q_test_001"
    count = await _times_missed(db_session, user_id, q_id)
    assert count == 0


@pytest.mark.asyncio
async def test_times_missed_counts_only_wrong(db_session: AsyncSession):
    user_id = _uid()
    q_id = "q_test_002"

    # Create a study session
    sess_id = _uid()
    db_session.add(StudySession(
        id=sess_id,
        user_id=user_id,
        mode="study",
        started_at=datetime.now(UTC),
        questions_answered=3,
        correct_count=1,
        xp_earned=0,
        max_combo=0,
    ))
    # Two wrong responses
    db_session.add(Response(id=_uid(), session_id=sess_id, question_id=q_id,
                             correct=False, grade=0, response_time_ms=1000,
                             created_at=datetime.now(UTC)))
    db_session.add(Response(id=_uid(), session_id=sess_id, question_id=q_id,
                             correct=False, grade=0, response_time_ms=1200,
                             created_at=datetime.now(UTC)))
    # One correct response (should NOT be counted)
    db_session.add(Response(id=_uid(), session_id=sess_id, question_id=q_id,
                             correct=True, grade=3, response_time_ms=800,
                             created_at=datetime.now(UTC)))
    await db_session.flush()

    count = await _times_missed(db_session, user_id, q_id)
    assert count == 2


@pytest.mark.asyncio
async def test_times_missed_ignores_other_users(db_session: AsyncSession):
    user_a = _uid()
    user_b = _uid()
    q_id = "q_test_003"

    sess_a = _uid()
    sess_b = _uid()
    db_session.add(StudySession(id=sess_a, user_id=user_a, mode="study",
                                 started_at=datetime.now(UTC),
                                 questions_answered=1, correct_count=0, xp_earned=0, max_combo=0))
    db_session.add(StudySession(id=sess_b, user_id=user_b, mode="study",
                                 started_at=datetime.now(UTC),
                                 questions_answered=1, correct_count=0, xp_earned=0, max_combo=0))
    db_session.add(Response(id=_uid(), session_id=sess_a, question_id=q_id,
                             correct=False, grade=0, response_time_ms=500,
                             created_at=datetime.now(UTC)))
    db_session.add(Response(id=_uid(), session_id=sess_b, question_id=q_id,
                             correct=False, grade=0, response_time_ms=500,
                             created_at=datetime.now(UTC)))
    await db_session.flush()

    # user_a missed once, user_b missed once — each should see only their own
    assert await _times_missed(db_session, user_a, q_id) == 1
    assert await _times_missed(db_session, user_b, q_id) == 1
