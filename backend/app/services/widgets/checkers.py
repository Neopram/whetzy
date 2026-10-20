"""Checkers deterministas de las preguntas `interactive` (40.1, `docs/PLAN_EXPERIENCIA.md` §1).

Una pregunta `interactive` lleva `{widget, params, target, checker}`: el widget
pinta el estado inicial a partir de `params`, el alumno lo manipula, el cliente
manda el estado serializado (`widget_state`) y el servidor lo compara con
`target` usando el checker nombrado. El resultado entra en BKT, Elo y FSRS como
cualquier otra respuesta.

Los mismos checkers viven en `frontend/src/widgets/checkers.ts`: el cliente
vuelve a corregir con el `target` que le devuelve la respuesta y avisa si su
veredicto no coincide con el del servidor. Los dos lados leen los mismos casos
de `backend/tests/fixtures/widget_checker_cases.json`, así que cambiar uno sin
el otro pone en rojo su test.

La igualdad es la de JSON, igual en los dos lenguajes: un booleano no es un
número (en Python `True == 1`; en JS `true !== 1`), `1` y `1.0` son el mismo
número, y un objeto es igual a otro si tiene las mismas claves con valores
iguales.

Este módulo no importa nada de la app: `scripts/check_question_bank.py` lo
carga por ruta para validar el banco sin arrancar la base de datos.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def json_equal(a: Any, b: Any) -> bool:
    """Igualdad estructural de dos valores JSON, sin las coerciones de Python."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, int | float) and isinstance(b, int | float):
        return a == b
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(json_equal(x, y) for x, y in zip(a, b, strict=True))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(json_equal(a[k], b[k]) for k in a)
    return False


def exact(state: Any, target: Any) -> bool:
    """El estado es exactamente el objetivo (p. ej. la secuencia de sondeos de una búsqueda binaria)."""
    return json_equal(state, target)


def unordered(state: Any, target: Any) -> bool:
    """Las dos listas tienen los mismos elementos, en cualquier orden y con sus repeticiones.

    Para resultados de un JOIN: las filas cuentan, su orden no.
    """
    if not isinstance(state, list) or not isinstance(target, list) or len(state) != len(target):
        return False
    remaining = list(target)
    for item in state:
        for i, candidate in enumerate(remaining):
            if json_equal(item, candidate):
                del remaining[i]
                break
        else:
            return False
    return True


CHECKERS: dict[str, Callable[[Any, Any], bool]] = {
    "exact": exact,
    "unordered": unordered,
}

SPEC_KEYS = ("widget", "params", "target", "checker")


def spec_problems(spec: Any) -> list[str]:
    """Lo que le falta a un `interactive` para poder corregirse; vacío si está bien."""
    if not isinstance(spec, dict):
        return ["interactive no es un objeto {widget, params, target, checker}"]
    problems = []
    missing = [k for k in SPEC_KEYS if k not in spec]
    if missing:
        problems.append(f"faltan {missing}")
    extra = sorted(set(spec) - set(SPEC_KEYS))
    if extra:
        problems.append(f"claves desconocidas {extra}")
    widget = spec.get("widget")
    if not isinstance(widget, str) or not widget.strip():
        problems.append("widget vacío o no es texto")
    if "params" in spec and not isinstance(spec["params"], dict):
        problems.append("params no es un objeto")
    if "target" in spec and spec["target"] is None:
        problems.append("target es null: no hay contra qué corregir")
    checker = spec.get("checker")
    if checker not in CHECKERS:
        problems.append(f"checker {checker!r} desconocido; los válidos son {sorted(CHECKERS)}")
    elif spec.get("target") is not None and not CHECKERS[checker](spec["target"], spec["target"]):
        # El objetivo tiene que aprobarse a sí mismo; si no, nadie puede acertar.
        problems.append(f"el target no aprueba su propio checker {checker!r}")
    return problems


def check(spec: dict[str, Any] | None, state: Any) -> bool:
    """Veredicto del servidor. Sin especificación válida o sin estado, la respuesta es incorrecta."""
    if spec is None or state is None or spec_problems(spec):
        return False
    return CHECKERS[spec["checker"]](state, spec["target"])
