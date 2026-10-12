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
        # Dos heads no son «la última»: el 2026-10-11 tumbaron producción y esta
        # función devolvía una de ellas, así que check_docs daba verde.
        if len(heads) > 1:
            return "multiple:" + ",".join(sorted(heads))
        return heads[0] if heads else "unknown"
    except Exception:
        return "unknown"


def _questions_by_track() -> dict[str, list[dict]]:
    by_track: dict[str, list[dict]] = {}
    for qdir in sorted((CONTENT / "questions").iterdir()):
        if not qdir.is_dir():
            continue
        m = re.match(r"(track\d+)", qdir.name)
        if not m:
            continue
        tid = m.group(1)
        for qfile in sorted(qdir.glob("*.json")):
            payload = json.loads(qfile.read_text(encoding="utf-8"))
            items = payload if isinstance(payload, list) else payload.get("questions", [])
            by_track.setdefault(tid, []).extend(items)
    return by_track


def _exec_types() -> frozenset[str]:
    return frozenset({"python_exec", "sql_exec", "js_exec", "fill_blank"})


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

    q_by_track = _questions_by_track()
    exec_types = _exec_types()

    certifications = []
    per_track = []
    for t in tracks:
        tid = t.get("id", t.get("track_id", ""))
        qs = q_by_track.get(tid, [])
        total_q = len(qs)
        exec_q = sum(1 for q in qs if q.get("type") in exec_types)
        ratio = round(exec_q / total_q * 100, 1) if total_q > 0 else 0.0

        entry = {
            "track_id": tid,
            "name_es": t.get("name_es", ""),
            "questions": total_q,
            "exec_questions": exec_q,
            "exec_pct": ratio,
            "is_certification": t.get("is_certification", False),
        }
        per_track.append(entry)
        if t.get("is_certification"):
            bp_file = CONTENT / "certifications" / f"{tid}.json"
            entry["has_blueprint"] = bp_file.exists()
            certifications.append(entry)

    return {
        "commit": commit,
        "tracks": len(tracks),
        "skills": len(skill_ids),
        "courses": courses,
        "lessons": len(lesson_skill_ids),
        "questions": sum(len(qs) for qs in q_by_track.values()),
        "glossary_terms": _count_glossary_terms(),
        "migrations": _count_migrations(),
        "alembic_head": _alembic_head(),
        "certifications": certifications,
        "per_track": per_track,
    }


if __name__ == "__main__":
    data = snapshot()
    compact = "--raw" in sys.argv
    print(json.dumps(data) if compact else json.dumps(data, indent=2))
