"""Los tests `slow` no se pueden quedar huérfanos (decisión del dueño 2026-09-30).

`pytest.ini` deselecciona `-m slow` de la suite por defecto a propósito — el
de BM25 (`test_rag_self_retrieval.py`) tarda solo él >5 min, y arrastrarlo en
cada corrida hace que "correr la suite" deje de ser rápido y la gente empiece
a saltarse la puerta. Pero deseleccionar sin correrlo EN NINGUNA PARTE sería
peor que no marcarlo: un test real (11.1, calidad del índice RAG + memoria)
dejaría de protegerse sin que nadie lo notara. Esta guarda comprueba que
`scripts/ci_local.sh` y `.github/workflows/ci.yml` lo sigan corriendo en su
propio paso, no que el paso pase (eso lo hace el paso mismo).
"""

from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PYTEST_INI = RAIZ / "backend" / "pytest.ini"
CI_LOCAL = RAIZ / "scripts" / "ci_local.sh"
CI_YML = RAIZ / ".github" / "workflows" / "ci.yml"


def test_addopts_deselecciona_slow_por_defecto() -> None:
    texto = PYTEST_INI.read_text(encoding="utf-8")
    addopts = next(linea for linea in texto.splitlines() if linea.strip().startswith("addopts"))
    assert "not slow" in addopts, (
        f"addopts ya no deselecciona `slow`: {addopts!r} — la suite por defecto "
        "volvería a arrastrar el tiempo del test de BM25 (>5 min solo)"
    )


def test_slow_esta_registrado_como_marcador() -> None:
    texto = PYTEST_INI.read_text(encoding="utf-8")
    assert "slow:" in texto, "el marcador `slow` ya no está declarado en pytest.ini"


def test_ci_local_corre_los_tests_lentos_en_su_propio_paso() -> None:
    texto = CI_LOCAL.read_text(encoding="utf-8")
    assert "pytest tests/ -m slow" in texto, (
        "scripts/ci_local.sh ya no tiene un paso que corra `-m slow` — los tests "
        "lentos (p. ej. el de BM25) dejarían de correr en el nivel 2 local"
    )


def test_ci_yml_corre_los_tests_lentos_en_su_propio_paso() -> None:
    texto = CI_YML.read_text(encoding="utf-8")
    assert "pytest tests/ -m slow" in texto, (
        ".github/workflows/ci.yml ya no tiene un paso que corra `-m slow` — los "
        "tests lentos dejarían de correr en GitHub Actions"
    )
