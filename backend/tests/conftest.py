"""Shared test fixtures for the Whetzy backend.

Provides function-scoped, isolated SQLite in-memory DB per test, a full
FastAPI AsyncClient, and ready-to-use user / auth-header / content fixtures.

The env overrides at the top of this file are intentionally set BEFORE any
app import so that settings and db.engine pick them up on first load.
"""

from __future__ import annotations

# ── MUST run before any `app.*` import ────────────────────────────────────────
import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-00000000000000000001")
os.environ.setdefault("GROQ_API_KEY", "")
os.environ.setdefault("AUTH_RATE_LIMIT", "200")
os.environ.setdefault("DEFAULT_RATE_LIMIT", "2000")
# ──────────────────────────────────────────────────────────────────────────────

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.content import Module, Question, Skill, Track
from app.models.user import User

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


# ── DB engine — one per test function, fully isolated ─────────────────────────


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(_TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with factory() as session:
        yield session


# ── FastAPI HTTPX client with get_db override ─────────────────────────────────


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── User + auth ───────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"test-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"tester{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Test User",
        language="es",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.fixture
def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


# ── Minimal content seed: Track → Module → Skill → Question ──────────────────


@pytest_asyncio.fixture
async def content_seed(db_session: AsyncSession) -> dict:
    """One complete content hierarchy ready for engine / quiz / glossary tests."""
    track = Track(
        id="track01",
        name_es="Python básico",
        name_en="Python basics",
        order=1,
        icon="🐍",
        color="#3776AB",
        total_questions=1,
    )
    mod = Module(
        id="m0101",
        track_id="track01",
        name_es="Variables",
        name_en="Variables",
        order=1,
        description_es="",
        description_en="",
    )
    skill = Skill(
        id="sk010101",
        module_id="m0101",
        name_es="Variables básicas",
        name_en="Basic variables",
        order=1,
    )
    question = Question(
        id="q010101001",
        skill_id="sk010101",
        type="mcq",
        difficulty_tier="easy",
        question_es="¿Qué imprime print(type(42))?",
        question_en="What does print(type(42)) print?",
        options_es=["<class 'int'>", "<class 'str'>", "<class 'float'>"],
        options_en=["<class 'int'>", "<class 'str'>", "<class 'float'>"],
        correct_index=0,
        explanation_es="42 es un entero.",
        explanation_en="42 is an integer.",
        source="CPython docs 3.13 — Built-in Types",
        elo_rating=1200.0,
    )
    db_session.add_all([track, mod, skill, question])
    await db_session.commit()
    return {
        "track_id": track.id,
        "module_id": mod.id,
        "skill_id": skill.id,
        "question_id": question.id,
    }
