"""Una misma afirmación verdadero/falso tiene una sola clave (39.29).

En track42 la clave de las V/F no dependía de la afirmación: «VPN encripta
comunicación» salía Verdadero en una copia y Falso en la siguiente (127 de 153
preguntas en grupos incoherentes), y ninguna guarda lo veía porque cada
pregunta, sola, estaba bien formada.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict

from app.services.content_loader import _content_root

# Prefijo de contexto «En X: …» y sufijos cosméticos que usaba el generador.
_CONTEXT = re.compile(r"^[^:]{3,60}:\s+")


def _statement(text: str) -> str:
    t = _CONTEXT.sub("", text.strip()).strip("¿?¡!. ").lower()
    return re.sub(r"\s+", " ", t)


def inconsistent() -> list[str]:
    keys: dict[tuple[str, str], set[int]] = defaultdict(set)
    ids: dict[tuple[str, str], list[str]] = defaultdict(list)
    root = _content_root() / "questions"
    for qfile in sorted(root.rglob("*.json")):
        payload = json.loads(qfile.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else payload.get("questions", [])
        for q in items:
            if q.get("type") != "true_false" or not isinstance(
                q.get("correct_index"), int
            ):
                continue
            k = (qfile.relative_to(root).parts[0], _statement(q.get("question_es", "")))
            keys[k].add(q["correct_index"])
            ids[k].append(q["id"])
    return [f"{t}: {s!r} {ids[(t, s)]}" for (t, s), v in keys.items() if len(v) > 1]


def test_the_same_statement_always_has_the_same_key() -> None:
    bad = inconsistent()
    assert not bad, f"{len(bad)} afirmaciones V/F con claves distintas: {bad[:5]}"
