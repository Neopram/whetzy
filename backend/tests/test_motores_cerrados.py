"""Todo test que abre un engine de SQLAlchemy tiene que cerrarlo.

`create_async_engine("sqlite+aiosqlite://...")` levanta un
`_connection_worker_thread` de aiosqlite, y ese hilo **no es demonio**: solo
muere si alguien llama a `dispose()`. Un engine sin cerrar no rompe ningun test
—todos pasan— pero deja el hilo esperando en `tx.get()` y **el proceso de pytest
no sale nunca**.

Eso paso el 2026-09-20: `tests/integration/test_rag_self_retrieval.py` abria tres
engines (uno por test) y no cerraba ninguno. La suite imprimia «1021 passed» y se
quedaba colgada indefinidamente, sin devolver codigo de salida. Una puerta que
espera un codigo que no llega es una puerta que no protege nada: `ci_local.sh`
habria dicho «CORRIENDO» para siempre.

Costo horas encontrarlo porque no se parece a un fallo: la suite esta en verde.
Se localizo volcando los hilos vivos tras `pytest.main()` — exactamente uno
no-demonio, `Thread-343 (_connection_worker_thread)`.

La primera version de esta guarda contaba texto: `texto.count(".dispose()")`.
Un `.dispose()` en un comentario o en un docstring la dejaba contenta —y de
hecho `conftest.py` menciona `create_async_engine(...)` en un docstring—. Ahora
se cuentan **llamadas** en el AST: comentarios y strings no existen ahi.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_RAIZ_TESTS = Path(__file__).resolve().parent


def _llamadas_a(arbol: ast.AST, nombre: str) -> int:
    """Cuantas veces se LLAMA a `nombre` (como `nombre(...)` o `x.nombre(...)`)."""
    total = 0
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        f = nodo.func
        es_nombre = isinstance(f, ast.Name) and f.id == nombre
        es_atributo = isinstance(f, ast.Attribute) and f.attr == nombre
        if es_nombre or es_atributo:
            total += 1
    return total


def _arbol(modulo: Path) -> ast.AST:
    return ast.parse(modulo.read_text(encoding="utf-8"), filename=str(modulo))


def _modulos_que_abren_engines() -> list[Path]:
    candidatos = sorted(
        set(_RAIZ_TESTS.rglob("test_*.py")) | set(_RAIZ_TESTS.rglob("conftest.py"))
    )
    return [
        p
        for p in candidatos
        if p.name != Path(__file__).name
        and _llamadas_a(_arbol(p), "create_async_engine") > 0
    ]


def test_hay_modulos_que_comprobar() -> None:
    """Si el descubrimiento se rompe, el de abajo pasaria sin mirar nada."""
    assert _modulos_que_abren_engines(), "no encuentro ningun test que abra engines"


@pytest.mark.parametrize("modulo", _modulos_que_abren_engines(), ids=lambda p: p.name)
def test_quien_abre_un_engine_lo_cierra(modulo: Path) -> None:
    arbol = _arbol(modulo)
    abiertos = _llamadas_a(arbol, "create_async_engine")
    cerrados = _llamadas_a(arbol, "dispose")

    assert cerrados >= 1, (
        f"{modulo.name} llama {abiertos} vez/veces a `create_async_engine(` y "
        f"nunca a `.dispose()` (llamadas reales; un `.dispose()` en un comentario "
        f"no cuenta). Cada engine de aiosqlite deja vivo un hilo NO demonio, asi "
        f"que pytest terminara los tests en verde y el proceso no saldra: la suite "
        f"se cuelga sin codigo de salida. Cierralo en un `finally`, en una fixture, "
        f"o con `async with`"
    )
