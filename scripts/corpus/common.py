"""Rutas y utilidades compartidas del pipeline de corpus (37.3)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "corpus"
INDEX = ROOT / "content" / "sources" / "index.json"


def source_dir(name: str, corpus: Path = CORPUS) -> Path:
    return corpus / name


def read_meta(src: Path) -> dict[str, Any]:
    p = src / ".meta.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def write_meta(src: Path, **fields: Any) -> dict[str, Any]:
    meta = read_meta(src)
    meta.update(fields)
    (src / ".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return meta


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
