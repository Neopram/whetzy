"""Every field `content_loader` reads with `data["..."]` exists in the content.

`scripts/start.sh` runs the loader under `set -e`, so one lesson or exam domain
missing a required key kills the container before gunicorn starts and Railway
answers 502 for the whole API. That is what `ec97405` did on 2026-09-26: track41
and track44-46 exam domains without `order` (and `percentage` instead of
`weight_pct`), and 146 lessons written as `content_es`/`name_es` without
`source`. The existing content tests only counted lessons per skill, so they
stayed green while production was down.
"""

from __future__ import annotations

import json
from typing import Any

from app.services.content_loader import _content_root

LESSON_REQUIRED = ("id", "skill_id", "title_es", "title_en", "body_es", "body_en", "source")
DOMAIN_REQUIRED = ("id", "name_es", "name_en", "weight_pct", "order")


def _tracks() -> list[dict[str, Any]]:
    data = json.loads(
        (_content_root() / "curriculum" / "tracks.json").read_text(encoding="utf-8")
    )
    return data["tracks"] if isinstance(data, dict) else data


def test_every_lesson_has_the_fields_the_loader_requires() -> None:
    broken: list[str] = []
    ids: dict[str, str] = {}
    for lfile in sorted((_content_root() / "lessons").rglob("*.json")):
        payload = json.loads(lfile.read_text(encoding="utf-8"))
        for lesson in payload if isinstance(payload, list) else [payload]:
            missing = [k for k in LESSON_REQUIRED if not lesson.get(k)]
            if missing:
                broken.append(f"{lfile.name}: {missing}")
                continue
            if lesson["id"] in ids:
                broken.append(f"{lfile.name}: duplicate id {lesson['id']} (also {ids[lesson['id']]})")
            ids[lesson["id"]] = lfile.name
    assert not broken, f"{len(broken)} lessons would crash the loader: {broken[:10]}"


def test_every_declared_exam_domain_has_the_fields_the_loader_requires() -> None:
    broken = [
        f"{t['id']}/{d.get('id')}: {[k for k in DOMAIN_REQUIRED if k not in d]}"
        for t in _tracks()
        for d in t.get("exam_domains") or []
        if any(k not in d for k in DOMAIN_REQUIRED)
    ]
    assert not broken, f"exam domains would crash the loader: {broken}"
