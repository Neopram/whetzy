#!/usr/bin/env python3
"""project_snapshot.py — 31.0: single source of truth for project figures.

Emits a JSON object with the canonical counts read from content/ and backend/.
check_docs.py imports this instead of duplicating the counting logic.

Usage:
    python scripts/project_snapshot.py          # pretty JSON to stdout
    python scripts/project_snapshot.py --raw    # compact JSON, one line
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
CONTENT = ROOT / "content"


def _count_questions() -> int:
    total = 0
    for qfile in sorted((CONTENT / "questions").rglob("*.json")):
        payload = json.loads(qfile.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else payload.get("questions", [])
        total += len(items)
    return total


def _count_glossary_terms() -> int:
    total = 0
    for gfile in sorted((CONTENT / "glossary").rglob("*.json")):
        payload = json.loads(gfile.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            total += len(payload)
        else:
            total += len(payload.get("terms", payload.get("entries", [])))
    return total


def _count_migrations() -> int:
    versions_dir = BACKEND / "alembic" / "versions"
    if not versions_dir.exists():
        return 0
    return len(
        [
            p
            for p in versions_dir.glob("*.py")
            if re.search(r"^revision(?::\s*str)?\s*=", p.read_text(encoding="utf-8"), re.M)
        ]
    )


def _alembic_head() -> str:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "heads"],
            cwd=BACKEND,
            capture_output=True,
            text=True,
            timeout=60,
        )
        heads = re.findall(r"^([0-9a-z_]{6,})\s*\(head\)", result.stdout, re.M)
        return heads[-1] if heads else "unknown"
    except Exception:
        return "unknown"


def snapshot() -> dict:
    curriculum = json.loads(
        (CONTENT / "curriculum" / "tracks.json").read_text(encoding="utf-8")
    )
    tracks = curriculum["tracks"] if isinstance(curriculum, dict) else curriculum

    skill_ids: set[str] = set()
    for t in tracks:
        for m in t.get("modules", []):
            for s in m.get("skills", []):
                skill_ids.add(s["id"] if isinstance(s, dict) else s)

    lesson_skill_ids: set[str] = set()
    for lfile in sorted((CONTENT / "lessons").rglob("*.json")):
        lesson = json.loads(lfile.read_text(encoding="utf-8"))
        if lesson.get("skill_id"):
            lesson_skill_ids.add(lesson["skill_id"])

    courses = sum(len(t.get("modules", [])) for t in tracks)

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        commit = result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        commit = "unknown"

    return {
        "commit": commit,
        "tracks": len(tracks),
        "skills": len(skill_ids),
        "courses": courses,
        "lessons": len(lesson_skill_ids),
        "questions": _count_questions(),
        "glossary_terms": _count_glossary_terms(),
        "migrations": _count_migrations(),
        "alembic_head": _alembic_head(),
    }


if __name__ == "__main__":
    data = snapshot()
    compact = "--raw" in sys.argv
    print(json.dumps(data) if compact else json.dumps(data, indent=2))
