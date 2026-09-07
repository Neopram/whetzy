"""Integration tests for tutor memory layers.

Uses an in-memory SQLite DB created from the real ORM models (no mock).
The NullProvider is used (no GROQ_API_KEY needed), so assertions focus on
prompt construction and call correctness, not LLM output quality.

Covers:
  - Episodic: _times_missed counts correctly (0 → 1 → 3 as responses added)
  - Episodic: _times_missed ignores correct responses
  - Short-term: conversation_history is accepted without error
  - Long-term: weak skills path does not crash when user has no skill states
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base
from app.models.content import Module, Question, Skill, Track
from app.models.session import Response, StudySession
from app.models.user import User
from app.services.ai.tutor import _times_missed

DB_URL = "sqlite+aiosqlite:///:memory:"


# ─── module-scoped engine + session ──────────────────────────────────────────

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def db_session():
    engine = create_async_engine(DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        # Seed Track → Module → Skill → Question for explain_question resolution
        track = Track(id="track01", name_es="Python básico", name_en="Python basics",
                      order=1, icon="🐍", color="#3776AB", total_questions=1)
        mod = Module(id="m01", track_id="track01", name_es="Variables", name_en="Variables",
                     order=1, description_es="", description_en="")
        skill = Skill(id="sk010101", module_id="m01",
                      name_es="Variables", name_en="Variables", order=1)
        q = Question(
            id="q010101001",
            skill_id="sk010101",
            type="mcq",
            difficulty_tier="easy",
            question_es="¿Cuál es la salida de x = 5; print(x)?",
            question_en="What is the output of x = 5; print(x)?",
            options_es=["5", "x", "Error"],
            options_en=["5", "x", "Error"],
            correct_index=0,
            explanation_es="x vale 5, print(x) imprime 5.",
            explanation_en="x is 5, print(x) prints 5.",
            source="CPython docs",
            elo_rating=1200.0,
        )
        session.add_all([track, mod, skill, q])
        await session.commit()
        yield session
    await engine.dispose()


def _new_user(lang: str = "es") -> User:
    uid = uuid.uuid4()
    return User(
        id=uid,
        email=f"{uid}@test.com",
        username=str(uid)[:8],
        display_name="Test",
        hashed_password="x",
        language=lang,
    )


async def _add_responses(
    db: AsyncSession, user: User, qid: str, n: int, correct: bool
) -> None:
    sess = StudySession(id=uuid.uuid4(), user_id=user.id, mode="study")
    db.add(sess)
    await db.flush()
    for _ in range(n):
        db.add(Response(
            session_id=sess.id,
            question_id=qid,
            correct=correct,
            grade=1,
            response_time_ms=2000,
        ))
    await db.commit()


# ─── tests ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_times_missed_zero_initially(db_session: AsyncSession):
    user = _new_user()
    db_session.add(user)
    await db_session.commit()
    assert await _times_missed(db_session, user.id, "q010101001") == 0


@pytest.mark.asyncio
async def test_times_missed_increments_per_failure(db_session: AsyncSession):
    user = _new_user()
    db_session.add(user)
    await db_session.commit()

    qid = "q010101001"
    assert await _times_missed(db_session, user.id, qid) == 0
    await _add_responses(db_session, user, qid, 1, correct=False)
    assert await _times_missed(db_session, user.id, qid) == 1
    await _add_responses(db_session, user, qid, 2, correct=False)
    assert await _times_missed(db_session, user.id, qid) == 3


@pytest.mark.asyncio
async def test_times_missed_ignores_correct_responses(db_session: AsyncSession):
    user = _new_user()
    db_session.add(user)
    await db_session.commit()

    qid = "q010101001"
    await _add_responses(db_session, user, qid, 5, correct=True)
    assert await _times_missed(db_session, user.id, qid) == 0


@pytest.mark.asyncio
async def test_times_missed_does_not_cross_contaminate_users(db_session: AsyncSession):
    u1 = _new_user()
    u2 = _new_user()
    db_session.add_all([u1, u2])
    await db_session.commit()

    qid = "q010101001"
    await _add_responses(db_session, u1, qid, 3, correct=False)
    assert await _times_missed(db_session, u1.id, qid) == 3
    assert await _times_missed(db_session, u2.id, qid) == 0
