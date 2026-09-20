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
"""

from __future__ import annotations

from pathlib import Path

import pytest

_RAIZ_TESTS = Path(__file__).resolve().parent


def _modulos_que_abren_engines() -> list[Path]:
    return sorted(
        p
        for p in _RAIZ_TESTS.rglob("test_*.py")
        if "create_async_engine(" in p.read_text(encoding="utf-8")
    )


def test_hay_modulos_que_comprobar() -> None:
    """Si el descubrimiento se rompe, el de abajo pasaria sin mirar nada."""
    assert _modulos_que_abren_engines(), "no encuentro ningun test que abra engines"


@pytest.mark.parametrize(
    "modulo", _modulos_que_abren_engines(), ids=lambda p: p.name
)
def test_quien_abre_un_engine_lo_cierra(modulo: Path) -> None:
    texto = modulo.read_text(encoding="utf-8")
    abiertos = texto.count("create_async_engine(")
    cerrados = texto.count(".dispose()")

    assert cerrados >= 1, (
        f"{modulo.name} llama {abiertos} vez/veces a `create_async_engine(` y "
        f"nunca a `.dispose()`. Cada engine de aiosqlite deja vivo un hilo NO "
        f"demonio, asi que pytest terminara los tests en verde y el proceso no "
        f"saldra: la suite se cuelga sin codigo de salida. Cierralo en un "
        f"`finally`, en una fixture, o con `async with`"
    )
