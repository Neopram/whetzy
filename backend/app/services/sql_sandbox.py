"""43.6 (ADR-65 D8): los pasos SQL de un proyecto se validan en el servidor.

Misma regla que el worker del navegador (`frontend/public/sql-worker.js`): el
código del alumno y luego el `test_code` del paso se ejecutan en una base
SQLite nueva en memoria, y el paso pasa si no hay error ni se agota el tiempo.

Encierro:
- sin ficheros: `temp_store = MEMORY` y el autorizador deniega ATTACH/DETACH (que es también lo que
  pide `VACUUM INTO 'fichero'`) y los PRAGMA fuera de una lista de consulta;
  las extensiones están desactivadas por defecto en `sqlite3`;
- sin red: SQLite no tiene funciones de red;
- con tiempo: el manejador de progreso aborta la sentencia al pasar el límite;
- con tamaño: `max_page_count` acota la base y `SQLITE_LIMIT_LENGTH` cada valor,
  que además acota el tiempo de una sola llamada;
- con memoria: `hard_heap_limit` acota lo que SQLite reserva (ordenaciones y
  tablas temporales en memoria, que `max_page_count` no ve). Es un límite del
  proceso, no de la conexión: el backend solo usa SQLite aquí, y dos
  ejecuciones a la vez lo comparten.

Python y JS no se ejecutan aquí: no hay sandbox para ellos (decisión del
dueño, 2026-10-17).
"""

from __future__ import annotations

import asyncio
import sqlite3
import time
from dataclasses import dataclass

TIME_LIMIT_S = 2.0
MAX_CODE_CHARS = 20_000  # lo que envía el alumno (lo valida el schema)
MAX_SCRIPT_CHARS = 100_000  # alumno + test_code del paso
MAX_PAGES = 2_560  # 10 MB con páginas de 4 KB
# Tope de cada valor. El reloj solo se mira entre instrucciones de la VM, así
# que el coste de UNA llamada (un `replace` es cuadrático) tiene que ser
# pequeño: con 1 MB, un solo `replace` tardaba 6 s con el límite en 2 s; con
# 16 KB, el peor caso que cabe en 20.000 caracteres de código tarda ~0,8 s
# (cuarto §7 de 43.6, 2026-10-17, medido).
MAX_VALUE_BYTES = 16_000
MAX_HEAP_BYTES = 64 * 1024 * 1024
# Instrucciones de la VM entre comprobaciones del reloj. Con 1000, un bucle de
# llamadas caras (`trim` de 16 KB, ~45 ms) metía ~100 entre dos comprobaciones
# y pasaba de 2 s a ~4 s; con 100 el exceso medido es ≤ 0,15 s y una ordenación
# de 1e6 filas pasa de ~0,35 s a ~0,45 s (quinto §7 de 43.6, 2026-10-17).
_PROGRESS_EVERY = 100

# Lo que un ejercicio de SQL puede querer mirar; nada que cambie el motor.
_READ_PRAGMAS = frozenset(
    {"table_info", "table_xinfo", "index_list", "index_info", "foreign_key_list"}
)
_DENIED = frozenset({sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH})


@dataclass(frozen=True)
class SqlCheck:
    passed: bool
    error: str | None = None
    timed_out: bool = False


def _authorizer(action: int, arg1: str | None, *_: object) -> int:
    if action in _DENIED:
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_PRAGMA and (arg1 or "").lower() not in _READ_PRAGMAS:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def has_statement(sql: str) -> bool:
    """True si a `sql` le queda algo que ejecutar fuera de blancos, `;` y comentarios.

    Basta el primer carácter fuera de un comentario: `SELECT '--'` cuenta.
    """
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        if c.isspace() or c == ";":
            i += 1
        elif sql.startswith("--", i):
            end = sql.find("\n", i)
            i = n if end < 0 else end + 1
        elif sql.startswith("/*", i):
            end = sql.find("*/", i + 2)
            i = n if end < 0 else end + 2
        else:
            return True
    return False


def check_sql(code: str, test: str, time_limit_s: float = TIME_LIMIT_S) -> SqlCheck:
    """Ejecuta `code` y luego `test` en una base nueva en memoria; pasa si no hay error.

    Son dos scripts sobre la misma conexión, no uno concatenado: un `/*` sin
    cerrar en el código del alumno convertía el test del paso en comentario y
    el paso pasaba sin ejecutar nada (§7 de 43.6, 2026-10-17). Y sin test que
    ejecutar no se aprueba: un paso con el test vacío, en blanco o solo
    comentarios pasaba sin comprobar nada (segundo §7, mismo día).
    """
    if len(code) + len(test) > MAX_SCRIPT_CHARS:
        return SqlCheck(passed=False, error="code too long")
    if not has_statement(test):
        return SqlCheck(passed=False, error="step has no test")
    conn = sqlite3.connect(":memory:", isolation_level=None, check_same_thread=False)
    deadline = time.monotonic() + time_limit_s
    expired = False

    def _progress() -> int:
        nonlocal expired
        expired = time.monotonic() > deadline
        return 1 if expired else 0

    try:
        conn.execute(f"PRAGMA max_page_count = {MAX_PAGES}")
        # Ordenaciones e índices temporales en memoria, no en ficheros de /tmp.
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute(f"PRAGMA hard_heap_limit = {MAX_HEAP_BYTES}")
        conn.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, MAX_VALUE_BYTES)
        conn.setlimit(sqlite3.SQLITE_LIMIT_ATTACHED, 0)
        conn.set_authorizer(_authorizer)
        conn.set_progress_handler(_progress, _PROGRESS_EVERY)
        conn.executescript(code)
        conn.executescript(test)
    except sqlite3.Error as exc:
        if expired:
            return SqlCheck(passed=False, timed_out=True)
        return SqlCheck(passed=False, error=str(exc))
    except ValueError as exc:
        # `executescript` rechaza un carácter nulo con ValueError, no sqlite3.Error.
        return SqlCheck(passed=False, error=str(exc))
    except MemoryError:
        # Al pasar `hard_heap_limit`, SQLite devuelve SQLITE_NOMEM y Python lo
        # convierte en MemoryError, no en sqlite3.Error (tercer §7 de 43.6).
        return SqlCheck(passed=False, error="out of memory")
    finally:
        conn.close()
    return SqlCheck(passed=True)


async def check_sql_async(
    code: str, test: str, time_limit_s: float = TIME_LIMIT_S
) -> SqlCheck:
    """`check_sql` en un hilo: el límite de tiempo lo pone el propio SQLite."""
    return await asyncio.to_thread(check_sql, code, test, time_limit_s)
