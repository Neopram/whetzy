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
from app.services.sql_sandbox import check_sql, has_statement

BASE = "/api/v1/projects"

SQL_TEST_1 = "SELECT CASE WHEN (SELECT COUNT(*) FROM pets) = 2 THEN 1 ELSE json('roto') END;"
# Para los tests del encierro: lo que vigilan está en el código, no en el test.
NO_OP = "SELECT 1;"
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


@pytest.mark.parametrize(
    "code",
    [
        "/* no escribo nada",  # comentario sin cerrar: se tragaba el test del paso
        "/* a medias */ /*",
        "CREATE TABLE pets(name TEXT); /*",
    ],
)
async def test_sql_un_comentario_sin_cerrar_no_se_traga_el_test(
    client, auth_headers, sql_project, code
):
    """§7 de 43.6 (2026-10-17): el código del alumno y el test del paso iban
    concatenados en un solo script; un `/*` sin cerrar convertía el test en
    comentario y el paso pasaba sin ejecutar ningún test."""
    await client.post(f"{BASE}/sql-pets/start", headers=auth_headers)
    r = await _submit(client, auth_headers, "sql-pets", 1, code, True)
    assert r.status_code == 200, r.text
    assert r.json()["step_passed"] is False
    assert r.json()["current_step"] == 1 and r.json()["completed"] is False


@pytest.mark.parametrize("test", ["", "-- falta el test"])
async def test_sql_un_paso_sin_test_no_se_aprueba(client, auth_headers, db_session, test):
    """Segundo §7 de 43.6: un paso con `test_code` vacío o solo comentarios
    pasaba con cualquier código, aunque el cliente dijera `passed: true`."""
    await _project(db_session, "sql-sin-test", "sql", [test])
    await client.post(f"{BASE}/sql-sin-test/start", headers=auth_headers)
    r = await _submit(client, auth_headers, "sql-sin-test", 1, SQL_OK_1, True)
    assert r.status_code == 200, r.text
    assert r.json()["step_passed"] is False
    assert r.json()["completed"] is False


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
    assert check_sql(SQL_OK_1, SQL_TEST_1).passed
    falla = check_sql("CREATE TABLE pets(name TEXT);", SQL_TEST_1)
    assert not falla.passed and falla.error


def test_sandbox_corta_un_bucle_infinito():
    t0 = time.monotonic()
    r = check_sql(
        "WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM n) "
        "SELECT COUNT(*) FROM n;",
        NO_OP,
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
    r = check_sql(sql.format(f=f), NO_OP)
    assert not r.passed
    assert not os.path.exists(f)


def test_sandbox_deniega_pragmas_que_cambian_el_motor_y_deja_los_de_consulta():
    assert not check_sql("PRAGMA max_page_count = 100000000;", NO_OP).passed
    assert not check_sql("PRAGMA writable_schema = ON;", NO_OP).passed
    assert check_sql("CREATE TABLE t(a); PRAGMA table_info(t);", NO_OP).passed


def test_sandbox_acota_el_tamano():
    r = check_sql(
        "CREATE TABLE t(a); WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM n "
        "LIMIT 200000) INSERT INTO t SELECT randomblob(500) FROM n;",
        NO_OP,
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


def test_sandbox_ejecuta_el_test_aparte_del_codigo_del_alumno():
    """El test del paso corre como script propio sobre la misma base: nada del
    alumno (un comentario o una cadena sin cerrar) puede tragárselo."""
    assert check_sql(SQL_OK_1, SQL_TEST_1).passed
    assert not check_sql("/* nada", SQL_TEST_1).passed
    assert not check_sql("CREATE TABLE pets(name TEXT); /*", SQL_TEST_1).passed
    assert not check_sql(SQL_OK_1, "SELECT json('roto');").passed


@pytest.mark.parametrize("test", ["", "   ", ";", "-- sin test", "/* nada */", "/* a */ -- b\n ;"])
def test_sandbox_sin_test_ejecutable_no_aprueba(test):
    """Segundo §7 de 43.6 (2026-10-17): con el test del paso vacío, en blanco o
    solo comentarios, el paso pasaba sin comprobar nada. Sin test que ejecutar,
    el servidor no aprueba."""
    r = check_sql(SQL_OK_1, test)
    assert not r.passed
    assert r.error


def test_sandbox_un_caracter_nulo_falla_sin_500():
    """Un `\\x00` en el código hacía saltar `ValueError` sin capturar (500)."""
    r = check_sql("CREATE TABLE pets(a);\x00 x", SQL_TEST_1)
    assert not r.passed
    assert r.error


@pytest.mark.parametrize("test", ["SELECT 1", "-- comprueba\nSELECT 1;", "/* x */ SELECT '--';"])
def test_has_statement_ve_la_sentencia_tras_los_comentarios(test):
    assert has_statement(test)
    assert check_sql(SQL_OK_1, test).passed



def test_sandbox_acota_la_memoria_de_una_ordenacion():
    """Tercer §7 de 43.6 (2026-10-17): ordenar blobs grandes crece en memoria sin
    que `max_page_count` lo vea (~550 MB en 2 s, medido); sin memoria libre
    `MemoryError` escapaba y el endpoint daba 500. Con `hard_heap_limit` falla
    pronto, como error del paso."""
    t0 = time.monotonic()
    r = check_sql(
        "WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM n LIMIT 20000) "
        "SELECT randomblob(15000) AS b FROM n ORDER BY b;",
        NO_OP,
    )
    assert not r.passed and not r.timed_out
    assert r.error == "out of memory"
    assert time.monotonic() - t0 < 1.5
    # El límite no estorba a un ejercicio normal.
    assert check_sql(SQL_OK_1, SQL_TEST_1).passed


def test_sandbox_acota_el_coste_de_una_sola_llamada():
    """Cuarto §7 de 43.6 (2026-10-17): el reloj solo se mira entre instrucciones
    de la VM, y un `replace` sobre un valor de ~1 MB tardaba 6 s en una sola
    instrucción con el límite en 2 s (medido). Con los valores acotados a
    `MAX_VALUE_BYTES` cada llamada cuesta milisegundos."""
    big = check_sql("SELECT randomblob(16001);", NO_OP)
    assert not big.passed and "too big" in (big.error or "")
    t0 = time.monotonic()
    check_sql(
        "SELECT length(replace(printf('%.*c', 999000, 'a'), "
        "printf('%.*c', 499000, 'a') || 'b', 'x'));",
        NO_OP,
    )
    assert time.monotonic() - t0 < 1.0


def test_sandbox_mira_el_reloj_a_menudo():
    """Quinto §7 de 43.6 (2026-10-17): con el reloj mirado cada 1000
    instrucciones, un bucle de `trim` caros (~45 ms cada uno con valores de
    16 KB) metía ~100 llamadas entre dos comprobaciones y pasaba de 2 s a ~4 s
    (medido). Tres pasadas con un límite de 0,3 s: el exceso depende de dónde
    caiga la comprobación, y una sola podría acertar por suerte."""
    code = (
        "WITH RECURSIVE c(i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM c WHERE i < 100000) "
        "SELECT count(trim(substr(replace(hex(zeroblob(7999)), '0', 'a'), 1, 15998 + i * 0), "
        "replace(hex(zeroblob(575)), '0', 'b') || 'a')) FROM c;"
    )
    worst = 0.0
    for _ in range(3):
        t0 = time.monotonic()
        r = check_sql(code, NO_OP, time_limit_s=0.3)
        worst = max(worst, time.monotonic() - t0)
        assert r.timed_out and not r.passed
    assert worst < 1.0


def test_sandbox_corta_una_fila_con_muchas_llamadas_caras():
    """Sexto §7 de 43.6 (2026-10-18): SQLite no mira el reloj entre las
    expresiones de una misma fila, así que una fila con muchas llamadas caras
    (aquí 20 `LIKE` de un patrón de 7.800 caracteres sobre 15.800) no se cortaba:
    3,8 s con el límite en 2 s y aprobaba; con 100 llamadas, 19 s (medido). El
    límite lo pone ahora un proceso hijo que se mata al vencer el plazo."""
    likes = ", ".join(["v LIKE p"] * 20)
    code = (
        "WITH s(v, p) AS (SELECT hex(zeroblob(7900)), "
        "'%' || substr(hex(zeroblob(7900)), 1, 7800) || 'x') "
        f"SELECT {likes} FROM s;"
    )
    t0 = time.monotonic()
    r = check_sql(code, NO_OP, time_limit_s=0.5)
    assert r.timed_out and not r.passed
    assert time.monotonic() - t0 < 1.5
