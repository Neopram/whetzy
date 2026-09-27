#!/usr/bin/env python3
"""Marca preguntas cuya opción correcta pudo quedar en otra ranura tras reescribirlas.

Uso: python scripts/content_qa/check_key_drift.py BASE_DIR NEW_DIR
Para cada pregunta compara la correcta original (ES y EN) con cada opción nueva; si
otra opción se le parece más que la marcada, la marca como sospechosa. El 26-09 el
reescritor dejó la correcta en la ranura 0 sin tocar correct_index en todo mod3002
(52 de 60 preguntas). Una clave original ya falsa también se marca: se lee a mano.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import jaccard, load_items


def drift(base_dir: Path, new_dir: Path) -> list[str]:
    hits = []
    for bf in sorted(base_dir.rglob("*.json")):
        nf = new_dir / bf.relative_to(base_dir)
        if not nf.exists():
            continue
        base = {q["id"]: q for q in load_items(bf) if "options_en" in q}
        for q in load_items(nf):
            b = base.get(q.get("id"))
            if not b or "options_en" not in q:
                continue
            ref_en = b["options_en"][b["correct_index"]]
            ref_es = b["options_es"][b["correct_index"]]
            score = [
                jaccard(ref_en, en) + jaccard(ref_es, es)
                for en, es in zip(q["options_en"], q["options_es"], strict=False)
            ]
            ci = q["correct_index"]
            best = max(range(len(score)), key=score.__getitem__)
            if best != ci and score[best] > score[ci]:
                hits.append(
                    f"{q['id']}: marcada[{ci}]={score[ci]:.2f} otra[{best}]={score[best]:.2f} "
                    f"| {q['options_en'][ci]!r} vs {q['options_en'][best]!r}"
                )
    return hits


def main(argv: list[str]) -> int:
    hits = drift(Path(argv[0]), Path(argv[1]))
    print("\n".join(hits))
    print(f"sospechosas: {len(hits)}")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
