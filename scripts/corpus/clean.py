"""Extrae texto de una fuente aceptada, deduplica por hash y la asigna a un track.

Solo trabaja sobre fuentes con `accepted: true` en su `.meta.json`: una fuente
rechazada por licencia no se procesa ni se deja «a medias».

* Texto: `.md`, `.rst`, `.txt`, `.py` tal cual; `.html` sin etiquetas.
* Gutenberg: se quitan la cabecera y el pie de la marca registrada («*** START
  OF…» / «*** END OF…»); lo que es de dominio público es el libro, no la marca.
* Dedup: SHA-256 del texto normalizado; el mismo contenido en dos rutas cuenta
  una vez.

    python -m scripts.corpus.clean --name thealgorithms-python --track track16
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from scripts.corpus.common import CORPUS, now_iso, read_meta, source_dir, write_meta

TEXT_EXT = {".md", ".rst", ".txt", ".py"}
HTML_EXT = {".html", ".htm"}
_PG_START = re.compile(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.IGNORECASE)
_PG_END = re.compile(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG EBOOK", re.IGNORECASE)


def extract(path: Path) -> str | None:
    ext = path.suffix.lower()
    if ext not in TEXT_EXT | HTML_EXT:
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    if ext in HTML_EXT:
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
    start, end = _PG_START.search(text), _PG_END.search(text)
    if start:
        text = text[start.end(): end.start() if end else None]
    text = re.sub(r"[ \t]+\n", "\n", text).strip()
    return text or None


def clean(src: Path, track: str) -> dict[str, int]:
    meta = read_meta(src)
    if not meta.get("accepted"):
        raise PermissionError(f"{src.name}: licencia no aceptada ({meta.get('license_reason', 'sin verificar')})")
    raw, out = src / "raw", src / "clean"
    out.mkdir(exist_ok=True)
    seen: set[str] = set()
    manifest = []
    kept = dupes = skipped = 0
    for path in sorted(p for p in raw.rglob("*") if p.is_file() and ".git" not in p.parts):
        text = extract(path)
        if text is None:
            skipped += 1
            continue
        digest = hashlib.sha256(re.sub(r"\s+", " ", text).encode("utf-8")).hexdigest()
        if digest in seen:
            dupes += 1
            continue
        seen.add(digest)
        (out / f"{digest[:16]}.txt").write_text(text, encoding="utf-8")
        manifest.append({"file": str(path.relative_to(raw)), "sha256": digest, "chars": len(text)})
        kept += 1
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    stats = {"kept": kept, "duplicates": dupes, "skipped": skipped}
    write_meta(src, track=track, cleaned_at=now_iso(), clean_stats=stats)
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name", required=True)
    ap.add_argument("--track", required=True, help="track de destino, p. ej. track16")
    ap.add_argument("--corpus", type=Path, default=CORPUS)
    a = ap.parse_args(argv)
    try:
        stats = clean(source_dir(a.name, a.corpus), a.track)
    except PermissionError as e:
        print(f"[clean] {e}")
        return 3
    print(f"[clean] {a.name} → {a.track}: {stats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
