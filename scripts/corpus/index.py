"""Escribe (o, con `--dry-run`, enseña) la entrada de una fuente en `content/sources/index.json`.

Solo entran fuentes con licencia aceptada. La entrada lleva URL, licencia leída
(SPDX), marca `reusar`, fecha de verificación, SHA del commit o del fichero y la
evidencia de licencia. Si la URL ya está, se actualiza en su sitio; el orden del
resto no cambia (diffs pequeños).

    python -m scripts.corpus.index --name thealgorithms-python --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.corpus.common import CORPUS, INDEX, read_meta, source_dir


def entry_for(meta: dict[str, Any], aliases: list[str] | None = None) -> dict[str, Any]:
    if not meta.get("accepted"):
        raise PermissionError(f"{meta.get('name')}: licencia no aceptada ({meta.get('license_reason', 'sin verificar')})")
    return {
        "url": meta["url"],
        "name": meta["name"],
        "license": meta["spdx"],
        "spdx": meta["spdx"],
        "mark": "reusar",
        "verified_date": str(meta["license_checked_at"])[:10],
        "sha": meta.get("sha"),
        "notes": f"Licencia leída en {meta.get('license_file')} por scripts/corpus (37.3): «{meta.get('license_evidence')}»",
        # URL donde se publica ESTE mismo contenido (p. ej. docs.python.org/3 para
        # el `Doc/` de cpython). Las preguntas citan la URL publicada, no el repo.
        **({"aliases": sorted({a.rstrip("/") for a in aliases})} if aliases else {}),
    }


def upsert(index: list[dict[str, Any]], entry: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    for i, e in enumerate(index):
        if str(e.get("url")).rstrip("/") == str(entry["url"]).rstrip("/"):
            new = list(index)
            new[i] = {**e, **entry}
            return new, "actualizada"
    return [*index, entry], "añadida"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name", required=True)
    ap.add_argument("--corpus", type=Path, default=CORPUS)
    ap.add_argument("--index", type=Path, default=INDEX)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--alias", action="append", default=[],
                    help="URL donde se publica este mismo contenido (repetible)")
    a = ap.parse_args(argv)
    meta = read_meta(source_dir(a.name, a.corpus))
    try:
        entry = entry_for(meta, a.alias)
    except PermissionError as e:
        print(f"[index] {e}")
        return 3
    index = json.loads(a.index.read_text(encoding="utf-8"))
    new, what = upsert(index, entry)
    if a.dry_run:
        print(f"[index] DRY-RUN — se {'añadiría' if what == 'añadida' else 'actualizaría'}:")
        print(json.dumps(entry, indent=2, ensure_ascii=False))
        return 0
    a.index.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[index] {a.name}: entrada {what} en {a.index}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
