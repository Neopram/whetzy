#!/usr/bin/env python3
"""Comprueba que una reescritura solo cambió los campos permitidos.

Uso: python scripts/content_qa/check_only_fields.py ORIG NEW --fields explanation_es,explanation_en
ORIG y NEW son ficheros o directorios con la misma estructura. Además: ninguna
explicación de plantilla (lista de audit_ai_traces) ni texto de explicación repetido
en 3 o más preguntas del mismo fichero.
"""

from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, load_items

_spec = importlib.util.spec_from_file_location(
    "aat", ROOT / "scripts" / "audit_ai_traces.py"
)
assert _spec and _spec.loader
_aat = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_aat)


def pairs(orig: Path, new: Path) -> list[tuple[Path, Path]]:
    if orig.is_file():
        return [(orig, new)]
    return [
        (f, new / f.relative_to(orig))
        for f in sorted(orig.rglob("*.json"))
        if (new / f.relative_to(orig)).exists()
    ]


def problems(orig: Path, new: Path, allowed: set[str]) -> list[str]:
    out = []
    for fo, fn in pairs(orig, new):
        a, b = load_items(fo), load_items(fn)
        if [q.get("id") for q in a] != [q.get("id") for q in b]:
            out.append(f"{fn.name}: ids u orden distintos")
            continue
        for qa, qb in zip(a, b, strict=True):
            out += [
                f"{qa['id']}.{k} cambió"
                for k in set(qa) | set(qb)
                if k not in allowed and qa.get(k) != qb.get(k)
            ]
            for k in ("explanation_es", "explanation_en"):
                if (qb.get(k) or "").strip().lower() in _aat.KNOWN_PLACEHOLDERS:
                    out.append(f"{qb['id']}.{k} es una plantilla")
        repeated = [
            t
            for t, n in Counter(
                (q.get("explanation_es") or "").strip() for q in b
            ).items()
            if t and n >= 3
        ]
        out += [
            f"{fn.name}: explicación repetida en 3+ preguntas: {t[:60]!r}"
            for t in repeated
        ]
    return out


def main(argv: list[str]) -> int:
    fields = (
        set(argv[argv.index("--fields") + 1].split(","))
        if "--fields" in argv
        else set()
    )
    found = problems(Path(argv[0]), Path(argv[1]), fields)
    print("\n".join(found))
    print("OK" if not found else f"FALLOS: {len(found)}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
