"""Piloto de widgets (40.2): el servidor corrige los ítems de demostración.

Los mismos casos de `tests/fixtures/widget_pilot_cases.json` los recorre el
cliente en `frontend/src/test/widgetsPiloto.test.tsx` (manipula el widget real,
serializa y corrige con `widgets/checkers.ts`). Que las dos listas de veredictos
salgan del mismo fichero es lo que impide que cliente y servidor discrepen.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.services.widgets.checkers import check, spec_problems

RAIZ = Path(__file__).resolve().parents[3]
PILOTO = json.loads((RAIZ / "backend" / "tests" / "fixtures" / "widget_pilot_cases.json").read_text("utf-8"))
REGISTRO = (RAIZ / "frontend" / "src" / "widgets" / "registry.ts").read_text("utf-8")


def _spec(item: dict) -> dict:
    return {k: item[k] for k in ("widget", "params", "target", "checker")}


def test_hay_los_tres_widgets_del_piloto() -> None:
    assert [i["widget"] for i in PILOTO["items"]] == ["binarySearch", "cidr", "sqlJoin"]


@pytest.mark.parametrize("item", PILOTO["items"], ids=lambda i: i["widget"])
def test_el_item_de_demo_es_una_spec_valida_y_el_widget_esta_registrado(item: dict) -> None:
    assert spec_problems(_spec(item)) == []
    assert re.search(rf"^\s*{item['widget']}\s*:\s*\(\)\s*=>\s*import\(", REGISTRO, re.MULTILINE)


@pytest.mark.parametrize(
    ("item", "caso"),
    [(i, c) for i in PILOTO["items"] for c in i["cases"]],
    ids=lambda x: x["widget"] if "widget" in x else x["why"],
)
def test_el_servidor_da_el_veredicto_esperado(item: dict, caso: dict) -> None:
    assert check(_spec(item), caso["state"]) is caso["expected"]


@pytest.mark.parametrize("item", PILOTO["items"], ids=lambda i: i["widget"])
def test_cada_widget_tiene_un_caso_correcto_y_uno_incorrecto(item: dict) -> None:
    assert {c["expected"] for c in item["cases"]} == {True, False}
