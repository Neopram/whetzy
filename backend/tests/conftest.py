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
# Generous limits above aren't isolation: Redis persists the hit counter
# across whole test RUNS (same key, same TTL window), not just across tests
# within one run. Two full-suite runs within the same ~60s window share a
# counter and both see 429s that neither earned on its own — found running
# the suite twice back to back this session. DATABASE_URL gets a fresh
# in-memory sqlite per run above; REDIS_URL gets the same treatment here:
# get_rate_limiter("") is falsy, so it returns InMemoryRateLimiter, which
# starts empty every process. The Redis backend itself is still exercised
# directly in test_rate_limiter.py, against an explicitly unreachable URL.
os.environ.setdefault("REDIS_URL", "")
# ──────────────────────────────────────────────────────────────────────────────

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# CRITICAL: Import all models BEFORE app.main so they're registered on Base
# when the app creates its engine
import app.models
from app.core.db import Base, get_db
from app.core.security import create_access_token, get_password_hash

# Now safe to import the app
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
    u.token = create_access_token(u.id)
    return u


@pytest.fixture
def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def plus_user(db_session: AsyncSession) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"plus-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"plus{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Plus User",
        language="es",
        is_premium=True,
        subscription_status="active",
        subscription_tier="plus",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.fixture
def plus_auth_headers(plus_user: User) -> dict[str, str]:
    token = create_access_token(plus_user.id)
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
@pytest_asyncio.fixture
async def owner(db_session: AsyncSession) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"owner-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"owner{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Owner User",
        language="es",
        role="owner",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    u.token = create_access_token(u.id)
    return u


def pytest_sessionfinish(session, exitstatus):
    """Cierra el engine GLOBAL de la app al acabar la sesion de tests.

    `app/core/db.py` crea `engine = create_async_engine(...)` al importarse, y en
    tests nadie lo cierra: `close_db()` solo lo llama el `lifespan` de FastAPI, y
    el cliente de tests usa `ASGITransport` sin lifespan. En cuanto algun test
    toca ese engine, aiosqlite levanta un `_connection_worker_thread` que **no es
    demonio** y que solo muere con `dispose()`.

    Sin esto, la suite termina en verde, imprime «N passed»... y **el proceso no
    sale nunca**: se queda con ese hilo esperando en `tx.get()`, sin devolver
    codigo de salida. Medido el 2026-09-20 volcando los hilos con faulthandler:
    exactamente uno, `Thread-346 (_connection_worker_thread)`.

    Va en `pytest_sessionfinish` y no en una fixture de sesion a proposito: aqui
    no hay bucle de eventos de pytest-asyncio de por medio.
    """
    import asyncio
    import logging

    from app.core import db as _db

    try:
        asyncio.run(_db.engine.dispose())
    except Exception:  # pragma: no cover - cerrar es best-effort
        # Si falla, el proceso se colgara al salir. Sin este log eso pasa
        # en silencio y parece otra vez «la suite no termina».
        logging.getLogger("whetzy.tests").exception(
            "no pude cerrar el engine global; el proceso puede no salir"
        )

    # ── La guarda de verdad ───────────────────────────────────────────────────
    # La comprobacion estructural (`tests/test_motores_cerrados.py`) mira los
    # ficheros de test, y el engine que colgo la suite el 2026-09-20 estaba en
    # `app/core/db.py`: no lo habria cazado. Esto mira el SINTOMA, que es lo que
    # importa — si sobrevive un hilo no-demonio, el proceso no sale y la puerta
    # se queda esperando un codigo que nunca llega.
    import threading

    colgados = [
        h
        for h in threading.enumerate()
        if h is not threading.current_thread() and not h.daemon and h.is_alive()
    ]
    if colgados:
        nombres = ", ".join(h.name for h in colgados)
        print(
            f"\n[hilos] {len(colgados)} hilo(s) NO demonio siguen vivos: {nombres}."
            "\n[hilos] El proceso no saldra: los tests pasan, se imprime el "
            "resumen, y pytest se queda colgado sin devolver codigo de salida."
            "\n[hilos] Casi siempre es un engine de SQLAlchemy sin `dispose()` "
            "- aiosqlite abre un hilo por conexion. Cierra el que hayas abierto."
        )
        session.exitstatus = 1
