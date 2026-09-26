"""Utilidades compartidas por las herramientas de QA de contenido."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STOP = frozenset(
    (
        "the",
        "a",
        "an",
        "of",
        "to",
        "and",
        "or",
        "in",
        "is",
        "are",
        "for",
        "with",
        "on",
        "by",
        "it",
        "that",
        "this",
        "be",
        "as",
        "not",
        "no",
        "its",
        "de",
        "la",
        "el",
        "en",
        "y",
        "o",
        "que",
        "los",
        "las",
        "un",
        "una",
        "es",
        "por",
        "con",
        "se",
        "del",
        "al",
        "para",
        "su",
        "lo",
    )
)


def load_items(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("questions", [data])


def tokens(text: str, drop_stop: bool = False) -> set[str]:
    words = set(re.findall(r"\w+", str(text).lower()))
    return {w for w in words if w not in STOP and len(w) > 2} if drop_stop else words


def jaccard(a: str, b: str) -> float:
    x, y = tokens(a), tokens(b)
    return len(x & y) / max(1, len(x | y))
