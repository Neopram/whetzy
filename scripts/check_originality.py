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

# Deuda medida el 2026-09-26 (12 parejas) y ampliada el 2026-09-29 al
# comparar tambien `code`/`code_es` (39.40/39.41): 16 parejas reales en total
# (track01 x3, track09 x5, track41 x13, track12 x3), todas reescritas con
# contenido genuinamente distinto y verificado. KNOWN vacio: nada que anotar.
# Se quita una pareja de aqui cuando se arregla; nunca se añade una nueva
# solo para tapar un hallazgo.
KNOWN: frozenset[frozenset[str]] = frozenset()


def _shingles(text: str) -> set[str]:
    words = re.findall(r"\w+", text.lower())
    return {" ".join(words[i : i + 3]) for i in range(max(1, len(words) - 2))}


def _content_text(q: dict[str, Any]) -> str:
    # code_output/exec questions (track09, track41...) often reuse a generic
    # boilerplate stem in question_es ("Cual es la salida usando modulos
    # estandar?") and put the actual differentiating snippet in `code`/
    # `code_es`. Comparing question_es alone both misses real duplicates
    # (two unrelated stems hide identical code) and flags false ones (two
    # unrelated snippets share a stem) - found working 39.27/39.40, where a
    # question_es-only comparison both missed 13 real track41 duplicates and
    # flagged unrelated questions that happened to share a boilerplate stem.
    return str(q.get("code") or q.get("code_es") or q.get("question_es", ""))


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
            by_track[_track(f)].append((q["id"], _shingles(_content_text(q)), _answer(q)))
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
