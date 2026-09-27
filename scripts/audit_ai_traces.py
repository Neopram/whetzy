#!/usr/bin/env python3
"""Huellas de generador en el contenido vivo (ledger 39.6).

`test_sin_relleno.py` (37.14) caza la pregunta de plantilla entera («Pregunta de
sk130102» con opciones A/B/C/D). Esto caza lo que queda cuando la pregunta es
real pero un campo lo rellenó el generador y nadie lo miró. Medido el
2026-09-26: 605 preguntas de track41, 42 y 44-46 muestran al alumno como
explicación «Explicación no disponible.», «Respuesta correcta basada en
documentación de Python.» o «Esta es la respuesta correcta según los principios
de Azure.», y pasaban todas las guardas porque la explicación existe y está en
los dos idiomas.

Huellas, por fichero:

* ``explicacion_plantilla``  explicación idéntica en ``REPEAT_LIMIT`` o más
  preguntas del banco vivo, o de la lista ``KNOWN_PLACEHOLDERS``. Una
  explicación que sirve para cientos de preguntas no explica ninguna.
* ``marcado_de_herramienta``  etiquetas de la herramienta del agente
  (``</invoke>``, ``<parameter``…) filtradas al texto.
* ``voz_de_asistente``        «As an AI», «Certainly!», «Aquí tienes»…

**Trinquete**: ``scripts/ai_traces_baseline.json`` guarda la cuenta por fichero
del 2026-09-26 y la escribe este script (``--write-baseline``), nunca una
persona. Un fichero puede bajar, nunca subir; un fichero sin línea base tiene
que estar a 0. Regenerar la base solo para fijar una mejora.

Uso::

    python scripts/audit_ai_traces.py                 # informe + código de salida
    python scripts/audit_ai_traces.py --write-baseline
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
LIVE_DIRS = ("questions", "lessons", "glossary")  # _quarantine no se carga
BASELINE = ROOT / "scripts" / "ai_traces_baseline.json"
REPEAT_LIMIT = 10

KNOWN_PLACEHOLDERS = {
    "explicación no disponible.",
    "explanation not available.",
    "respuesta correcta basada en documentación de python.",
    "correct answer based on python documentation.",
    "esta es la respuesta correcta según los principios de azure.",
    "this is the correct answer according to azure principles.",
    "reference source for detailed explanation",
    "ejecuta el código paso a paso.",
    "execute the code step by step.",
}
# Plantilla que cambia en cada pregunta y por eso no la ve el umbral de repetidas: «Explicación
# para ¿Desventajas PCA?» (356 preguntas en track20/21, hallado el 2026-09-27, 39.37).
TEMPLATE_PREFIX = re.compile(r"^(?:explicación para|explanation for)\b")
TOOL_MARKUP = re.compile(r"</?(?:invoke|parameter|function_calls|antml:[a-z_]+)\b")
ASSISTANT_VOICE = re.compile(
    r"\b(?:as an ai\b|certainly!|i hope this helps|como modelo de lenguaje|aquí tienes (?:la|el|una|un)\b)",
    re.IGNORECASE,
)
EXPLANATION_FIELDS = ("explanation_es", "explanation_en")


def _items(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    for key in ("questions", "terms"):
        if isinstance(data.get(key), list):
            return [x for x in data[key] if isinstance(x, dict)]
    return [data]


def _files() -> list[Path]:
    return [p for d in LIVE_DIRS for p in sorted((CONTENT / d).rglob("*.json"))]


def _strings(obj: Any) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in _strings(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in _strings(v)]
    return []


def traces(files: list[Path] | None = None) -> dict[str, Counter[str]]:
    files = _files() if files is None else files
    loaded = {p: _items(p) for p in files}
    freq: Counter[str] = Counter(
        (it.get(f) or "").strip().lower()
        for items in loaded.values()
        for it in items
        for f in EXPLANATION_FIELDS
        if (it.get(f) or "").strip()
    )
    out: dict[str, Counter[str]] = {}
    for path, items in loaded.items():
        c: Counter[str] = Counter()
        for it in items:
            for f in EXPLANATION_FIELDS:
                v = (it.get(f) or "").strip().lower()
                if v and (v in KNOWN_PLACEHOLDERS or freq[v] >= REPEAT_LIMIT or TEMPLATE_PREFIX.match(v)):
                    c["explicacion_plantilla"] += 1
            for s in _strings(it):
                if TOOL_MARKUP.search(s):
                    c["marcado_de_herramienta"] += 1
                if ASSISTANT_VOICE.search(s):
                    c["voz_de_asistente"] += 1
        if c:
            key = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
            out[key.as_posix()] = c
    return out


def regressions(
    found: dict[str, Counter[str]], base: dict[str, dict[str, int]]
) -> list[str]:
    bad = []
    for f, c in sorted(found.items()):
        for kind, n in sorted(c.items()):
            allowed = base.get(f, {}).get(kind, 0)
            if n > allowed:
                bad.append(f"{f}: {kind} {n} > {allowed}")
    return bad


def main(argv: list[str]) -> int:
    found = traces()
    if "--write-baseline" in argv:
        BASELINE.write_text(
            json.dumps(
                {f: dict(sorted(c.items())) for f, c in sorted(found.items())},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"[huellas] línea base escrita: {len(found)} ficheros")
        return 0
    base = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {}
    total: Counter[str] = Counter()
    for c in found.values():
        total.update(c)
    for f, c in sorted(found.items()):
        print(f"  {f}: " + ", ".join(f"{k}={v}" for k, v in sorted(c.items())))
    bad = regressions(found, base)
    print(
        f"[huellas] {dict(total)} en {len(found)} ficheros; {len(bad)} por encima de la línea base"
    )
    for b in bad[:20]:
        print("  SUBE", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
