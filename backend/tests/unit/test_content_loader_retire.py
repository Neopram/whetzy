"""Quitar un track de `tracks.json` lo retira; nunca borra el historial (S.12).

`content_loader` borraba en cada arranque los tracks que ya no estaban
declarados, y el borrado iba en cascada (`ondelete="CASCADE"`) desde `tracks`
hasta módulos, skills y preguntas, y de ahí hasta `responses`, los intentos de
examen, los certificados y las compras de certificación. En Postgres eso es
una línea de JSON borrando el historial de cada alumno de ese track.

El motor de los tests es SQLite, que no aplica las claves foráneas si no se
le pide: aquí se activa `PRAGMA foreign_keys=ON` para que el `CASCADE` haga lo
mismo que en producción y el test pueda ponerse en rojo de verdad.
"""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import event, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base
from app.models.content import Question, Track
from app.models.exam import Certificate, CertificationPurchase, MockExamAttempt
from app.models.session import Response, StudySession
from app.models.user import User
from app.services.content_loader import load_content
from app.services.quiz import _select_question

# Las tablas cuyo DELETE se llevaría historial de alumnos por cascada.
_CONTENT_DELETE = re.compile(r"^\s*DELETE\s+FROM\s+\"?(tracks|modules|skills|questions)\b", re.IGNORECASE)


def _track(tid: str, order: int) -> dict[str, Any]:
    n = tid[-2:]
    return {
        "id": tid,
        "name_es": f"Ruta {n}",
        "name_en": f"Track {n}",
        "order": order,
        "modules": [
            {
                "id": f"m{n}01",
                "name_es": "Módulo",
                "name_en": "Module",
                "skills": [{"id": f"sk{n}0101", "name_es": "Skill", "name_en": "Skill"}],
            }
        ],
    }


def _question(n: str) -> dict[str, Any]:
    return {
        "id": f"q{n}0101_001",
        "skill_id": f"sk{n}0101",
        "type": "mcq",
        "question_es": "¿Cuánto es 1 + 1?",
        "question_en": "What is 1 + 1?",
        "options_es": ["1", "2", "3", "4"],
        "options_en": ["1", "2", "3", "4"],
        "correct_index": 1,
        "explanation_es": "Uno más uno son dos.",
        "explanation_en": "One plus one is two.",
    }


def _write_content(root: Path, track_ids: list[str]) -> None:
    (root / "curriculum").mkdir(parents=True, exist_ok=True)
    (root / "questions").mkdir(parents=True, exist_ok=True)
    tracks = [_track(t, i) for i, t in enumerate(track_ids, start=1)]
    (root / "curriculum" / "tracks.json").write_text(
        json.dumps({"tracks": tracks}), encoding="utf-8"
    )
    # Las preguntas de los dos tracks se quedan en disco aunque el track salga
    # de `tracks.json`: es lo que pasa al poner uno en cuarentena.
    (root / "questions" / "bank.json").write_text(
        json.dumps([_question("98"), _question("99")]), encoding="utf-8"
    )


@pytest_asyncio.fixture
async def fk_session() -> AsyncGenerator[tuple[AsyncSession, list[str]], None]:
    """Sesión sobre SQLite con claves foráneas activas, y el SQL que emite."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    statements: list[str] = []

    @event.listens_for(engine.sync_engine, "connect")
    def _fk_on(dbapi_conn: Any, _record: Any) -> None:
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def _record(_conn: Any, _cur: Any, statement: str, *_args: Any) -> None:
        statements.append(statement)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        yield session, statements
    await engine.dispose()


async def _student_history(db: AsyncSession, track_id: str, question_id: str) -> None:
    user = User(
        id=uuid.uuid4(),
        email=f"s12-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"s12{uuid.uuid4().hex[:6]}",
        hashed_password="x",
        display_name="Alumna",
        language="es",
    )
    db.add(user)
    await db.flush()
    session = StudySession(user_id=user.id, track_id=track_id)
    db.add(session)
    await db.flush()
    db.add(Response(session_id=session.id, question_id=question_id, correct=True,
                    grade=3, response_time_ms=4000))
    now = datetime.now(UTC)
    attempt = MockExamAttempt(user_id=user.id, track_id=track_id, question_ids=[question_id],
                              duration_minutes=90, expires_at=now + timedelta(minutes=90),
                              submitted_at=now, status="submitted")
    db.add(attempt)
    await db.flush()
    db.add(Certificate(code=f"WHZ-{uuid.uuid4().hex[:10]}", user_id=user.id, track_id=track_id,
                       attempt_id=attempt.id, score_pct=80.0, questions=1))
    db.add(CertificationPurchase(user_id=user.id, track_id=track_id, price_usd=39.99,
                                 source="test"))
    await db.commit()


async def _counts(db: AsyncSession) -> dict[str, int]:
    out: dict[str, int] = {}
    for model in (Track, Question, Response, MockExamAttempt, Certificate, CertificationPurchase):
        out[model.__tablename__] = await db.scalar(select(func.count()).select_from(model)) or 0
    return out


@pytest.mark.asyncio
async def test_quitar_un_track_del_json_no_borra_historial(
    fk_session: tuple[AsyncSession, list[str]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, statements = fk_session
    monkeypatch.setenv("CONTENT_DIR", str(tmp_path))

    _write_content(tmp_path, ["track98", "track99"])
    await load_content(db)
    await _student_history(db, "track99", "q990101_001")
    before = await _counts(db)
    assert before["responses"] == before["certificates"] == 1

    statements.clear()
    _write_content(tmp_path, ["track98"])
    stats = await load_content(db)

    assert await _counts(db) == before, "retirar un track no puede borrar nada"
    assert stats["retired_tracks"] == 1
    retired = await db.get(Track, "track99")
    assert retired is not None and retired.is_active is False
    kept = await db.get(Track, "track98")
    assert kept is not None and kept.is_active is True

    # La guarda: el cargador no emite DELETE sobre el contenido. Un DELETE en
    # `tracks` es el que arrastraba todo lo demás.
    deletes = [s for s in statements if _CONTENT_DELETE.match(s)]
    assert not deletes, f"el cargador borra contenido: {deletes}"

    # Vuelve a la lista: se reactiva con su historial intacto.
    _write_content(tmp_path, ["track98", "track99"])
    stats = await load_content(db)
    assert stats["retired_tracks"] == 0
    await db.refresh(retired)
    assert retired.is_active is True
    assert await _counts(db) == before


@pytest.mark.asyncio
async def test_el_catalogo_no_ofrece_un_track_retirado(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession,
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONTENT_DIR", str(tmp_path))
    _write_content(tmp_path, ["track98", "track99"])
    await load_content(db_session)
    _write_content(tmp_path, ["track98"])
    await load_content(db_session)

    res = await client.get("/api/v1/content/tracks", headers=auth_headers)
    assert res.status_code == 200, res.text
    assert [t["id"] for t in res.json()] == ["track98"]

    res = await client.get("/api/v1/progress/dashboard", headers=auth_headers)
    assert res.status_code == 200, res.text
    assert [t["track_id"] for t in res.json()["tracks"]] == ["track98"]


@pytest.mark.asyncio
async def test_practica_y_repaso_no_sirven_preguntas_de_un_track_retirado(
    db_session: AsyncSession, user: User, content_seed: dict,
) -> None:
    question, _ = await _select_question(db_session, user, "sk010101")
    assert question is not None, "con el track activo la pregunta se sirve"

    track = await db_session.get(Track, "track01")
    assert track is not None
    track.is_active = False
    await db_session.commit()

    question, _ = await _select_question(db_session, user, "sk010101")
    assert question is None
