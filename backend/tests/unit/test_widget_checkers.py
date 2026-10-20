"""Checkers de `interactive` (40.1): el servidor y el cliente corrigen igual.

Los casos de `tests/fixtures/widget_checker_cases.json` los corre también
`frontend/src/test/widgetCheckers.test.ts` contra `frontend/src/widgets/checkers.ts`.
Un checker que cambia en un lado y no en el otro deja de dar el `expected` de
algún caso y pone su test en rojo: esa es la «discrepancia cliente↔servidor»
del criterio de 40.1.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.services.widgets import checkers
from app.services.widgets.checkers import CHECKERS, check, spec_problems

RAIZ = Path(__file__).resolve().parents[3]
CASOS = json.loads((RAIZ / "backend" / "tests" / "fixtures" / "widget_checker_cases.json").read_text("utf-8"))
CLIENTE = RAIZ / "frontend" / "src" / "widgets" / "checkers.ts"


@pytest.mark.parametrize("caso", CASOS["cases"], ids=lambda c: f"{c['checker']}:{c['why']}")
def test_cada_caso_da_su_veredicto(caso: dict) -> None:
    assert CHECKERS[caso["checker"]](caso["state"], caso["target"]) is caso["expected"]


def test_los_mismos_checkers_en_los_dos_lados() -> None:
    # Un checker nuevo en un solo lado sería una pregunta que uno corrige y el otro no.
    m = re.search(r"export const CHECKERS = \{([^}]*)\}", CLIENTE.read_text("utf-8"))
    assert m, "no encuentro `export const CHECKERS = { ... }` en checkers.ts"
    del_cliente = {n.strip() for n in m.group(1).split(",") if n.strip()}
    assert set(CHECKERS) == del_cliente == set(CASOS["checkers"])


def test_cada_checker_tiene_casos_de_los_dos_signos() -> None:
    # Sin un caso false, un checker que aprueba todo pasaría; sin uno true, uno que suspende todo.
    for name in CHECKERS:
        signos = {c["expected"] for c in CASOS["cases"] if c["checker"] == name}
        assert signos == {True, False}, name


SPEC = {"widget": "binarySearch", "params": {"items": [1, 3, 5, 7]}, "target": [3, 5], "checker": "exact"}


def test_spec_valida_no_tiene_problemas() -> None:
    assert spec_problems(SPEC) == []


@pytest.mark.parametrize(
    ("cambio", "contiene"),
    [
        ({"checker": "fuzzy"}, "checker 'fuzzy' desconocido"),
        ({"widget": ""}, "widget vacío"),
        ({"params": []}, "params no es un objeto"),
        ({"target": None}, "target es null"),
        ({"extra": 1}, "claves desconocidas"),
        ({"checker": "unordered", "target": {"a": 1}}, "no aprueba su propio checker"),
    ],
)
def test_spec_invalida_dice_por_que(cambio: dict, contiene: str) -> None:
    problemas = spec_problems({**SPEC, **cambio})
    assert any(contiene in p for p in problemas), problemas


def test_spec_sin_claves() -> None:
    assert any("faltan" in p for p in spec_problems({"widget": "x"}))
    assert spec_problems([1]) == ["interactive no es un objeto {widget, params, target, checker}"]


def test_check_del_servidor() -> None:
    assert check(SPEC, [3, 5]) is True
    assert check(SPEC, [5, 3]) is False
    # Sin estado o sin especificación válida, la respuesta es incorrecta: nunca se cree al cliente.
    assert check(SPEC, None) is False
    assert check(None, [3, 5]) is False
    assert check({**SPEC, "checker": "fuzzy"}, [3, 5]) is False


def test_el_modulo_no_importa_la_app() -> None:
    # `check_question_bank.py` lo carga por ruta, sin base de datos ni settings.
    fuente = Path(checkers.__file__).read_text("utf-8")
    assert "from app" not in fuente and "import app" not in fuente


def test_check_question_bank_valida_interactive(tmp_path: Path) -> None:
    # La puerta del banco usa los mismos checkers que el servidor.
    import sys

    sys.path.insert(0, str(RAIZ / "scripts"))
    import check_question_bank as cqb

    assert "interactive" in cqb.KNOWN_TYPES
    # Hasta 40.2 no hay widgets registrados: ninguna pregunta puede nombrar uno.
    assert cqb.registered_widgets() == frozenset()
    assert cqb.interactive_problems({"interactive": SPEC}) == [
        "widget 'binarySearch' no esta en frontend/src/widgets/registry.ts: nadie podria contestarla"
    ]
    cqb.registered_widgets.cache_clear()
    real = cqb.WIDGET_REGISTRY
    try:
        fake = tmp_path / "registry.ts"
        fake.write_text(
            "export const WIDGETS: Record<string, WidgetLoader> = {\n"
            "  binarySearch: () => import('./binarySearch'),\n};\n",
            "utf-8",
        )
        cqb.WIDGET_REGISTRY = fake
        assert cqb.interactive_problems({"interactive": SPEC}) == []
    finally:
        cqb.WIDGET_REGISTRY = real
        cqb.registered_widgets.cache_clear()
    assert cqb.interactive_problems({"interactive": {**SPEC, "checker": "fuzzy"}})
    assert cqb.interactive_problems({}) == ["interactive no es un objeto {widget, params, target, checker}"]
