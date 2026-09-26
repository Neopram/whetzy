#!/usr/bin/env python3
"""Devuelve la opción correcta a la posición que tenía en el repo.

Uso: python scripts/content_qa/rebalance_positions.py REWRITE_DIR REPO_QUESTIONS_DIR OUT_DIR TRACK...
La reescritura puede cambiar el orden; el repo ya tenía las posiciones repartidas. Si
en el repo las posiciones rotan 0,1,2,3… (plantilla, 18.14), el destino sale de un hash
del id. Las preguntas cuya explicación cita letras («(A)») no se mueven.
"""

from __future__ import annotations

import collections
import hashlib
import json
import re
import sys
from pathlib import Path

LETTER = re.compile(r"\([A-D]\)")


def main(argv: list[str]) -> int:
    rewrite, repo, out = map(Path, argv[:3])
    for track in argv[3:]:
        pos: collections.Counter[int] = collections.Counter()
        (out / track).mkdir(parents=True, exist_ok=True)
        for f in sorted((rewrite / track).glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            target = {
                q["id"]: q["correct_index"]
                for q in json.loads(
                    (repo / track / f.name).read_text(encoding="utf-8")
                )["questions"]
            }
            seq = list(target.values())
            if len(seq) >= 8 and all(v == i % 4 for i, v in enumerate(seq)):
                target = {
                    k: int(hashlib.sha1(k.encode()).hexdigest(), 16) % 4 for k in target
                }
            for q in data["questions"]:
                ci, tgt = q["correct_index"], target[q["id"]]
                if LETTER.search(
                    q.get("explanation_es", "") + q.get("explanation_en", "")
                ):
                    tgt = ci
                for k in ("options_es", "options_en"):
                    rest = [o for i, o in enumerate(q[k]) if i != ci]
                    rest.insert(tgt, q[k][ci])
                    q[k] = rest
                q["correct_index"] = tgt
                pos[tgt] += 1
            (out / track / f.name).write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        print(track, dict(sorted(pos.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
