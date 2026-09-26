#!/usr/bin/env python3
"""Casi-duplicados en el banco de preguntas (ledger 39.7).

`question_diversity.py` (37.0) cuenta enunciados **idénticos** tras normalizar y
tolera hasta un 10 % por track. No ve dos preguntas que dicen lo mismo con
otra puntuación o una palabra cambiada y que además tienen la misma respuesta:
para quien estudia es la misma pregunta dos veces, y para un generador de
contenido es la forma más barata de inflar un recuento.

Regla: dos preguntas del mismo track son casi-duplicadas si su respuesta
correcta es la misma y la similitud de Jaccard de sus enunciados (trigramas de
palabras, ES) es >= ``THRESHOLD``. Trinquete: las parejas que ya existían el
2026-09-26 están en ``KNOWN`` (deuda anotada); cualquier otra hace fallar.

Uso::

    python scripts/check_originality.py            # informe + código de salida
    python scripts/check_originality.py --list     # todas las parejas
"""

from __future__ import annotations

import itertools
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "content" / "questions"
THRESHOLD = 0.8

# Deuda medida el 2026-09-26: 12 parejas (track01, track09, track41).
# Se quita una pareja de aquí cuando se arregla; nunca se añade una nueva.
KNOWN: frozenset[frozenset[str]] = frozenset({
    frozenset({"q010101004", "q010602002"}),
    frozenset({"q010205007", "q010404005"}),
    frozenset({"q010604003", "q010604010"}),
    frozenset({"q090104mc002", "q090104mc008"}),
    frozenset({"q090301mc001", "q090302mc001"}),
    frozenset({"q090301mc002", "q090302mc004"}),
    frozenset({"q090301mc009", "q090302mc005"}),
    frozenset({"q090301mc010", "q090302mc009"}),
    frozenset({"q410101_069", "q410103_067"}),
    frozenset({"q410101_074", "q410103_072"}),
    frozenset({"q410102_070", "q410102_075"}),
    frozenset({"q410104_068", "q410104_073"}),
})


def _shingles(text: str) -> set[str]:
    words = re.findall(r"\w+", text.lower())
    return {" ".join(words[i : i + 3]) for i in range(max(1, len(words) - 2))}


def _answer(q: dict[str, Any]) -> str:
    opts = q.get("options_es")
    ci = q.get("correct_index")
    if opts and isinstance(ci, int) and 0 <= ci < len(opts):
        return str(opts[ci]).strip().lower()
    return str(q.get("correct_answer_es", "")).strip().lower()


def _track(path: Path) -> str:
    m = re.match(r"(track\d+)", path.relative_to(QUESTIONS).parts[0])
    return m.group(1) if m else path.parent.name


def pairs(root: Path = QUESTIONS) -> list[tuple[str, str, str, float]]:
    by_track: dict[str, list[tuple[str, set[str], str]]] = defaultdict(list)
    for f in sorted(root.rglob("*.json")):
        payload = json.loads(f.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else payload.get("questions", [])
        for q in items:
            by_track[_track(f)].append((q["id"], _shingles(q.get("question_es", "")), _answer(q)))
    found = []
    for track, qs in sorted(by_track.items()):
        for a, b in itertools.combinations(qs, 2):
            if a[2] != b[2]:
                continue
            sim = len(a[1] & b[1]) / max(1, len(a[1] | b[1]))
            if sim >= THRESHOLD:
                found.append((track, a[0], b[0], round(sim, 3)))
    return found


def new_pairs(found: list[tuple[str, str, str, float]]) -> list[tuple[str, str, str, float]]:
    return [p for p in found if frozenset((p[1], p[2])) not in KNOWN]


def main(argv: list[str]) -> int:
    found = pairs()
    fresh = new_pairs(found)
    if "--list" in argv:
        for p in found:
            print(*p)
    print(f"[originalidad] {len(found)} parejas casi-duplicadas, {len(fresh)} fuera de la deuda anotada")
    for p in fresh[:20]:
        print("  NUEVA", *p)
    return 1 if fresh else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
