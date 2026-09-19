"""Tests para scripts/ledger.py — el indice consultable del ledger.

Los cuatro casos que de verdad importan salieron de ejecutar el parser contra
el ledger real, no de imaginar entradas:

1. Una celda con `Request | None` dentro de backticks desplazaba todas las
   columnas de la fila 22.12 y hacia leer `DONE` como prosa.
2. Las series 25-29 usan una tabla de **tres** columnas y dejan el estado en
   una cita encima; un parser de cinco columnas se comia 48 filas en silencio.
3. `REGRESIÓN` y `RESUELTA` son estados reales del ledger que su propia
   cabecera no declara.
4. `11.10` es posterior a `11.9`, y el orden lexico dice lo contrario.

El ultimo test corre contra `docs/AUTONOMOUS_STATE.md` de verdad: si alguien
reformatea una tabla y el indice deja de encontrar filas, la siguiente sesion
volveria a leer 29.000 tokens sin enterarse.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "ledger.py"
REAL_LEDGER = ROOT / "docs" / "AUTONOMOUS_STATE.md"

assert SCRIPT.exists(), f"ledger.py no esta en {SCRIPT}"


@pytest.fixture(scope="module")
def mod():
    """Importa `scripts/ledger.py` por ruta.

    El `sys.modules[...] = module` **antes** de ejecutarlo no es decoracion:
    `@dataclass` resuelve las anotaciones con
    `sys.modules.get(cls.__module__).__dict__`, y un modulo cargado a mano y
    sin registrar no esta ahi, asi que la clase revienta al definirse.
    """
    spec = importlib.util.spec_from_file_location("ledger", SCRIPT)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules["ledger"] = module
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        yield module
    finally:
        sys.modules.pop("ledger", None)


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


FIVE_COLUMN = """# Ledger de prueba

## 0. Invariantes del sistema (no romper nunca)

| Invariante | Valor |
|---|---|
| Backend prod | `https://ejemplo.invalid` |
| Contenido | 10 preguntas / 2 tracks |

## 2. Backlog ejecutable

### 11 — Serie de prueba
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 11.9 | 2 | Novena | TODO | criterio nueve |
| 11.10 | 2 | Decima | TODO | criterio diez |
| 11.11 | 1 | Undecima | **DONE** — commit abc1234 | criterio once |
| 11.12 | 0 | Con `Request | None` dentro de backticks | **DONE 2026-09-19** | criterio doce |
| 11.13 | 0 | Bloqueada por humano | HUMAN-BLOCKED (H.10) | criterio trece |
| 11.14 | 0 | Bloqueada por dependencia | BLOCKED (11.13) | criterio catorce |
| 11.15 | 3 | Con tilde en el estado | **REGRESIÓN — ver 11.15x** | criterio quince |

## 3. Cola HUMAN-BLOCKED

| ID | Qué falta | Cómo se desbloquea |
|---|---|---|
| H.10 | Cohorte beta | Reclutar 30 personas |
"""

THREE_COLUMN = """# Ledger de prueba

## 2. Backlog ejecutable

### 28. Marketplace de instructores
> **Estado:** `BLOCKED (orden del dueño)` — abre cuando 22.1 esté DONE.
> **PRI:** 4. **Modelo:** Sonnet.

| ID | Tarea | Criterio DONE |
|---|---|---|
| 28.0 | Schema DB | Migración HEAD nueva |
| 28.1 | API CRUD | OpenAPI con las rutas |
"""


def _ledger_from(tmp_path: Path, text: str, mod):
    path = tmp_path / "AUTONOMOUS_STATE.md"
    path.write_text(text, encoding="utf-8")
    return mod.parse(path)


# --- el parser ------------------------------------------------------------


def test_pipe_dentro_de_backticks_no_desplaza_columnas(tmp_path, mod):
    """La fila 22.12 real: `Request | None` partia la celda en dos."""
    ledger = _ledger_from(tmp_path, FIVE_COLUMN, mod)
    task = ledger.by_id("11.12")
    assert task is not None
    assert task.state == "DONE", f"el estado se leyo como {task.state_raw!r}"
    assert task.criterion == "criterio doce"
    assert "None" in task.title


def test_tabla_de_tres_columnas_hereda_estado_y_pri_de_la_serie(tmp_path, mod):
    """Series 25-29: sin estas dos lineas se perdian 48 filas sin avisar."""
    ledger = _ledger_from(tmp_path, THREE_COLUMN, mod)
    assert len(ledger.tasks) == 2
    for task in ledger.tasks:
        assert task.state == "BLOCKED"
        assert task.pri == 4
    assert ledger.by_id("28.1").criterion == "OpenAPI con las rutas"


def test_estados_con_tilde_se_normalizan(tmp_path, mod):
    ledger = _ledger_from(tmp_path, FIVE_COLUMN, mod)
    assert ledger.by_id("11.15").state == "REGRESION"


def test_human_blocked_no_se_confunde_con_blocked(tmp_path, mod):
    """`BLOCKED` es sufijo de `HUMAN-BLOCKED`: el orden de comprobacion manda."""
    ledger = _ledger_from(tmp_path, FIVE_COLUMN, mod)
    assert ledger.by_id("11.13").state == "HUMAN-BLOCKED"
    assert ledger.by_id("11.14").state == "BLOCKED"


def test_orden_natural_de_ids(tmp_path, mod):
    """11.10 va despues de 11.9. El orden lexico dice lo contrario."""
    ledger = _ledger_from(tmp_path, FIVE_COLUMN, mod)
    ids = [t.id for t in ledger.series("11")]
    assert ids.index("11.9") < ids.index("11.10") < ids.index("11.11")


def test_next_excluye_lo_que_no_se_puede_coger(tmp_path, mod):
    ledger = _ledger_from(tmp_path, FIVE_COLUMN, mod)
    ids = [t.id for t in ledger.executable()]
    assert "11.11" not in ids, "una DONE no es trabajo pendiente"
    assert "11.13" not in ids, "una HUMAN-BLOCKED espera a una persona"
    assert "11.14" not in ids, "una BLOCKED espera a otra tarea"
    # Quedan 11.9 y 11.10 (PRI 2) y 11.15 (PRI 3): primero el PRI, luego el id.
    assert ids == ["11.9", "11.10", "11.15"]


def test_invariantes_se_leen_de_la_seccion_cero(tmp_path, mod):
    ledger = _ledger_from(tmp_path, FIVE_COLUMN, mod)
    assert ledger.invariants["Backend prod"] == "`https://ejemplo.invalid`"
    assert "10 preguntas" in ledger.invariants["Contenido"]
    assert "Invariante" not in ledger.invariants, "la cabecera no es un invariante"


def test_cola_human_blocked_se_parsea_aparte(tmp_path, mod):
    ledger = _ledger_from(tmp_path, FIVE_COLUMN, mod)
    assert [t.id for t in ledger.blocked] == ["H.10"]
    assert ledger.by_id("H.10").criterion == "Reclutar 30 personas"


# --- la CLI ---------------------------------------------------------------


def test_show_de_un_id_inexistente_falla(tmp_path, mod):
    result = _run(["show", "99.99"])
    assert result.returncode == 1
    assert "99.99" in result.stdout


def test_json_es_json(mod):
    result = _run(["--json", "next", "-n", "3"])
    assert result.returncode == 0
    rows = json.loads(result.stdout)
    assert len(rows) == 3
    assert {"id", "pri", "state", "criterion", "line"} <= set(rows[0])


def test_cost_publica_el_numero_que_justifica_el_script(mod):
    result = _run(["--json", "cost"])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["respuesta_next_tokens_aprox"] < data["ledger_tokens_aprox"] / 10, (
        "si el indice deja de ahorrar un orden de magnitud, no compensa mantenerlo"
    )


# --- contra el ledger de verdad -------------------------------------------


def test_el_ledger_real_parsea(mod):
    """Que el ledger siga siendo legible por maquina es un invariante.

    Sin esto, una sesion reformatea una tabla, el indice devuelve menos filas
    de las que hay y nadie se entera hasta que una tarea se queda sin hacer.
    """
    ledger = mod.parse(REAL_LEDGER)
    assert len(ledger.tasks) > 100, f"solo {len(ledger.tasks)} filas: la tabla cambio de forma"
    assert ledger.blocked, "la cola HUMAN-BLOCKED de la seccion 3 no se encuentra"
    assert "Alembic HEAD" in ledger.invariants
    assert all(t.state != "UNKNOWN" for t in ledger.tasks)


def test_check_pasa_contra_el_ledger_real():
    result = _run(["check"])
    assert result.returncode == 0, result.stdout
