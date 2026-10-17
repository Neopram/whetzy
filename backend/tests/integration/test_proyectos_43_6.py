"""43.6 (ADR-65 D8): el progreso de un proyecto vive en el servidor y se valida.

Antes: `submit-step` se creía `passed` y cualquier `step_number`; con
`{"step_number": <último>, "passed": true}` el proyecto quedaba completado sin
ejecutar nada, y la pantalla guardaba el progreso solo en memoria.

Decisión del dueño (2026-10-17): los pasos SQL se ejecutan en el servidor en
SQLite en memoria (sin red, sin ficheros, con tiempo) y el `passed` del cliente
se ignora; Python y JS siguen en el navegador, el servidor impone el orden y
guarda el código, y esas finalizaciones no cuentan como verificadas (no salen
en el perfil público) hasta que haya sandbox.
"""

from __future__ import annotations

import os
import time
import uuid

import pytest
from sqlalchemy import select

from app.models.project import Project, ProjectStep, ProjectSubmission
from app.services.sql_sandbox import check_sql

BASE = "/api/v1/projects"

SQL_TEST_1 = "SELECT CASE WHEN (SELECT COUNT(*) FROM pets) = 2 THEN 1 ELSE json('roto') END;"
SQL_TEST_2 = (
    "SELECT CASE WHEN (SELECT name FROM pets ORDER BY age DESC LIMIT 1) = 'Rex' "
    "THEN 1 ELSE json('roto') END;"
)
SQL_OK_1 = "CREATE TABLE pets(name TEXT, age INT); INSERT INTO pets VALUES ('Rex', 9), ('Mia', 2);"
SQL_OK_2 = SQL_OK_1 + " SELECT name FROM pets ORDER BY age DESC;"


async def _project(db, slug: str, runtime: str, tests: list[str]) -> Project:
    project = Project(
        id=uuid.uuid4(), slug=slug, track_id="track01", runtime=runtime,
        name_es="P", name_en="P", order=1,
    )
    db.add(project)
    for n, test in enumerate(tests, start=1):
        db.add(
            ProjectStep(
                id=uuid.uuid4(), project_id=project.id, step_number=n,
                title_es=f"Paso {n}", title_en=f"Step {n}",
                starter_code="-- tu código" if runtime == "sql" else "# tu código",
                test_code=test,
            )
        )
    await db.commit()
    return project


@pytest.fixture
async def sql_project(db_session):
    return await _project(db_session, "sql-pets", "sql", [SQL_TEST_1, SQL_TEST_2])


@pytest.fixture
async def py_project(db_session):
    return await _project(db_session, "py-hola", "python", ["assert hola() == 'hola'"] * 2)


async def _submit(client, headers, slug, n, code, passed):
    return await client.post(
        f"{BASE}/{slug}/submit-step",
        json={"step_number": n, "code": code, "passed": passed},
        headers=headers,
    )


# --- SQL: lo decide el servidor ---------------------------------------------------


async def test_sql_passed_true_con_codigo_que_no_pasa_no_avanza(client, auth_headers, sql_project):
    await client.post(f"{BASE}/sql-pets/start", headers=auth_headers)
    r = await _submit(client, auth_headers, "sql-pets", 1, "CREATE TABLE pets(name TEXT);", True)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["step_passed"] is False
    assert body["error"]
    assert body["current_step"] == 1 and body["completed"] is False


async def test_sql_el_servidor_aprueba_aunque_el_cliente_diga_que_no(
    client, auth_headers, sql_project
):
    await client.post(f"{BASE}/sql-pets/start", headers=auth_headers)
    r = await _submit(client, auth_headers, "sql-pets", 1, SQL_OK_1, False)
    assert r.json()["step_passed"] is True
    assert r.json()["current_step"] == 2


async def test_sql_completado_cuenta_como_verificado(client, auth_headers, sql_project):
    await client.post(f"{BASE}/sql-pets/start", headers=auth_headers)
    await _submit(client, auth_headers, "sql-pets", 1, SQL_OK_1, True)
    r = await _submit(client, auth_headers, "sql-pets", 2, SQL_OK_2, True)
    body = r.json()
    assert body["completed"] is True and body["verified"] is True


# --- Orden de los pasos -----------------------------------------------------------


async def test_saltar_al_ultimo_paso_es_409_y_no_completa(client, auth_headers, sql_project):
    await client.post(f"{BASE}/sql-pets/start", headers=auth_headers)
    r = await _submit(client, auth_headers, "sql-pets", 2, SQL_OK_2, True)
    assert r.status_code == 409
    prog = (await client.get(f"{BASE}/sql-pets/progress", headers=auth_headers)).json()
    assert prog["completed"] is False and prog["current_step"] == 1


async def test_enviar_tras_completar_es_409(client, auth_headers, sql_project):
    await client.post(f"{BASE}/sql-pets/start", headers=auth_headers)
    await _submit(client, auth_headers, "sql-pets", 1, SQL_OK_1, True)
    await _submit(client, auth_headers, "sql-pets", 2, SQL_OK_2, True)
    r = await _submit(client, auth_headers, "sql-pets", 2, SQL_OK_2, True)
    assert r.status_code == 409


# --- El progreso sobrevive a salir -------------------------------------------------


async def test_el_codigo_y_el_paso_se_guardan(client, auth_headers, sql_project):
    await client.post(f"{BASE}/sql-pets/start", headers=auth_headers)
    await _submit(client, auth_headers, "sql-pets", 1, SQL_OK_1, True)
    await _submit(client, auth_headers, "sql-pets", 2, "SELECT 1; -- a medias", True)
    prog = (await client.get(f"{BASE}/sql-pets/progress", headers=auth_headers)).json()
    assert prog["current_step"] == 2
    assert prog["step_code"] == {"1": SQL_OK_1, "2": "SELECT 1; -- a medias"}


# --- Python / JS: navegador, sin verificación -----------------------------------


async def test_python_passed_true_con_el_codigo_de_partida_no_avanza(
    client, auth_headers, py_project
):
    await client.post(f"{BASE}/py-hola/start", headers=auth_headers)
    r = await _submit(client, auth_headers, "py-hola", 1, "# tu código", True)
    assert r.json()["step_passed"] is False
    assert r.json()["current_step"] == 1


async def test_python_completado_no_es_verificado(
    client, auth_headers, user, db_session, py_project
):
    code = "def hola():\n    return 'hola'\n"
    await client.post(f"{BASE}/py-hola/start", headers=auth_headers)
    await _submit(client, auth_headers, "py-hola", 1, code, True)
    r = await _submit(client, auth_headers, "py-hola", 2, code, True)
    assert r.json()["completed"] is True and r.json()["verified"] is False

    sub = await db_session.scalar(
        select(ProjectSubmission).where(ProjectSubmission.user_id == user.id)
    )
    assert sub is not None and sub.completed and not sub.verified


async def test_codigo_demasiado_largo_es_422(client, auth_headers, sql_project):
    await client.post(f"{BASE}/sql-pets/start", headers=auth_headers)
    r = await _submit(client, auth_headers, "sql-pets", 1, "x" * 20_001, True)
    assert r.status_code == 422


# --- El encierro de SQLite ---------------------------------------------------------


def test_sandbox_pasa_y_falla_como_el_worker():
    assert check_sql(SQL_OK_1 + "\n\n" + SQL_TEST_1).passed
    falla = check_sql("CREATE TABLE pets(name TEXT);\n\n" + SQL_TEST_1)
    assert not falla.passed and falla.error


def test_sandbox_corta_un_bucle_infinito():
    t0 = time.monotonic()
    r = check_sql(
        "WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM n) "
        "SELECT COUNT(*) FROM n;",
        time_limit_s=0.5,
    )
    assert r.timed_out and not r.passed
    assert time.monotonic() - t0 < 3


@pytest.mark.parametrize(
    "sql",
    [
        "ATTACH DATABASE '{f}' AS x;",
        "CREATE TABLE t(a); VACUUM INTO '{f}';",
    ],
    ids=["attach", "vacuum-into"],
)
def test_sandbox_no_escribe_ficheros(sql, tmp_path):
    f = tmp_path / "fuga.db"
    r = check_sql(sql.format(f=f))
    assert not r.passed
    assert not os.path.exists(f)


def test_sandbox_deniega_pragmas_que_cambian_el_motor_y_deja_los_de_consulta():
    assert not check_sql("PRAGMA max_page_count = 100000000;").passed
    assert not check_sql("PRAGMA writable_schema = ON;").passed
    assert check_sql("CREATE TABLE t(a); PRAGMA table_info(t);").passed


def test_sandbox_acota_el_tamano():
    r = check_sql(
        "CREATE TABLE t(a); WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM n "
        "LIMIT 200000) INSERT INTO t SELECT randomblob(500) FROM n;",
        time_limit_s=10,
    )
    assert not r.passed and not r.timed_out
    assert "full" in (r.error or "")


def test_el_autorizador_deniega_attach_por_si_solo():
    # Dos capas: el autorizador y `SQLITE_LIMIT_ATTACHED = 0`. Cada una basta;
    # este test vigila la primera sin la segunda.
    import sqlite3

    from app.services.sql_sandbox import _authorizer

    conn = sqlite3.connect(":memory:")
    conn.set_authorizer(_authorizer)
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("ATTACH DATABASE ':memory:' AS x")
    conn.close()
