"""Cada trabajo de la cola se ejecuta una sola vez con dos workers (G).

`start.sh` arranca gunicorn con `--workers 2` y cada proceso lanza su propio
`job_worker_loop`. Sin bloqueo, los dos leían la misma cola y ejecutaban cada
trabajo dos veces; `run_payouts` es una liquidación a instructores.

- La guarda que corre siempre: la consulta de reclamo compila a
  `FOR UPDATE SKIP LOCKED` en Postgres, y un lote reclamado ya no está en cola.
- La prueba de dos workers a la vez necesita Postgres de verdad (SQLite no
  tiene bloqueo de filas). Corre si `WHETZY_TEST_POSTGRES_URL` apunta a una
  base con las migraciones aplicadas; si no, se salta.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from collections import Counter
from typing import Any

import pytest
from sqlalchemy import delete, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.job import Job
from app.models.user import User
from app.services import job_worker
from app.services.job_worker import (
    claim_pending_jobs,
    claim_query,
    process_pending_jobs,
)

_TEST_TYPE = "test_cuenta_ejecuciones"


def test_la_consulta_de_reclamo_bloquea_y_salta_lo_bloqueado() -> None:
    sql = str(claim_query(10).compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE SKIP LOCKED" in sql, sql


async def _user(db: AsyncSession) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"jobs-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"jobs{uuid.uuid4().hex[:6]}",
        hashed_password="x",
        display_name="Jobs",
        language="es",
    )
    db.add(u)
    await db.commit()
    return u


@pytest.mark.asyncio
async def test_un_lote_reclamado_ya_no_esta_en_cola(db_session: AsyncSession) -> None:
    user = await _user(db_session)
    # En SQLite un BIGINT de clave primaria no se autoincrementa: ids a mano.
    for job_id in (1, 2, 3):
        db_session.add(Job(id=job_id, user_id=user.id, job_type=_TEST_TYPE, payload={}))
    await db_session.commit()

    first = await claim_pending_jobs(db_session, max_jobs=10)
    assert len(first) == 3
    assert {j.status for j in first} == {"running"}
    assert await claim_pending_jobs(db_session, max_jobs=10) == []


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("WHETZY_TEST_POSTGRES_URL"),
    reason="la carrera entre dos workers solo se reproduce con bloqueo de filas (Postgres)",
)
async def test_dos_workers_a_la_vez_no_repiten_ningun_trabajo() -> None:
    engine = create_async_engine(os.environ["WHETZY_TEST_POSTGRES_URL"])
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    runs: Counter[int] = Counter()

    async def _handler(job: Job, db: AsyncSession) -> dict[str, Any]:
        runs[job.id] += 1
        await asyncio.sleep(0.01)  # el otro worker entra mientras este trabaja
        return {}

    job_worker._JOB_HANDLERS[_TEST_TYPE] = _handler
    try:
        async with factory() as db:
            user = await _user(db)
            db.add_all(Job(user_id=user.id, job_type=_TEST_TYPE, payload={}) for _ in range(40))
            await db.commit()
            ids = set((await db.scalars(select(Job.id).where(Job.user_id == user.id))).all())

        async def _worker() -> None:
            async with factory() as db:
                while await process_pending_jobs(db, max_jobs=5):
                    pass

        await asyncio.gather(_worker(), _worker())

        assert set(runs) == ids, "algún trabajo se quedó sin ejecutar"
        repeated = {job_id: n for job_id, n in runs.items() if n > 1}
        assert not repeated, f"trabajos ejecutados más de una vez: {repeated}"
    finally:
        job_worker._JOB_HANDLERS.pop(_TEST_TYPE, None)
        async with factory() as db:
            await db.execute(delete(Job).where(Job.job_type == _TEST_TYPE))
            await db.execute(delete(User).where(User.email.like("jobs-%@whetzy.test")))
            await db.commit()
        await engine.dispose()
