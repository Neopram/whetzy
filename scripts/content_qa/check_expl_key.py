#!/usr/bin/env python3
"""Marca preguntas cuya explicación se parece más a una opción incorrecta que a la marcada.

Uso: python scripts/content_qa/check_expl_key.py DIR
Complementa check_key_drift: sirve también cuando no hay base (la explicación es la
referencia). Da sospechosas; muchas son explicaciones que citan el distractor para
refutarlo.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import load_items, tokens

MARGIN = 0.34


def suspects(folder: Path) -> list[str]:
    hits = []
    for path in sorted(folder.rglob("*.json")):
        for q in load_items(path):
            if "options_en" not in q or not isinstance(q.get("correct_index"), int):
                continue
            ex = tokens(q.get("explanation_en", ""), drop_stop=True)
            score = [
                len(tokens(o, True) & ex) / max(1, len(tokens(o, True)))
                for o in q["options_en"]
            ]
            ci = q["correct_index"]
            best = max(range(len(score)), key=score.__getitem__)
            if best != ci and score[best] >= score[ci] + MARGIN:
                hits.append(
                    f"{q['id']}: marcada={score[ci]:.2f} otra[{best}]={score[best]:.2f}"
                )
    return hits


def main(argv: list[str]) -> int:
    hits = suspects(Path(argv[0]))
    print("\n".join(hits))
    print(f"sospechosas: {len(hits)}")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
