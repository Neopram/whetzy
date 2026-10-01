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


def _skill_ids() -> set[str]:
    return {s["id"] for t in _tracks() for m in t["modules"] for s in m["skills"]}


def test_every_glossary_term_reaches_a_track() -> None:
    """A term without `track_id` (file or term level) is silently skipped by the loader.

    On 2026-09-26 that was 286 of 1,044 terms (tracks 18, 20, 21, 23, 27, 44-46):
    the loader reported them as `skipped` and production served those tracks
    with no glossary.
    """
    track_ids = {t["id"] for t in _tracks()}
    broken: list[str] = []
    for gfile in sorted((_content_root() / "glossary").glob("*.json")):
        payload = json.loads(gfile.read_text(encoding="utf-8"))
        terms = payload if isinstance(payload, list) else payload.get("terms", [])
        file_track = None if isinstance(payload, list) else payload.get("track_id")
        for i, term in enumerate(terms):
            track = term.get("track_id", file_track)
            missing = [k for k in ("term_es", "term_en", "definition_es", "definition_en") if not term.get(k)]
            if track not in track_ids or missing:
                broken.append(f"{gfile.name}[{i}] track={track} missing={missing}")
    assert not broken, f"{len(broken)} glossary terms would be skipped or crash: {broken[:10]}"


def test_every_question_reaches_a_skill() -> None:
    skills = _skill_ids()
    broken: list[str] = []
    for qfile in sorted((_content_root() / "questions").rglob("*.json")):
        payload = json.loads(qfile.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else payload.get("questions", [])
        for q in items:
            missing = [k for k in ("id", "skill_id", "question_es", "question_en") if not q.get(k)]
            if missing or q.get("skill_id") not in skills:
                broken.append(f"{qfile.name}:{q.get('id')} missing={missing}")
    assert not broken, f"{len(broken)} questions would be skipped or crash: {broken[:10]}"


def test_every_track_icon_renders_as_an_icon() -> None:
    """TracksScreen pinta `icon` tal cual: «container» o «git-branch» salían como texto.

    11 tracks (18-23, 26-30) llevaban el nombre de un icono de una librería que
    el frontend no usa; el alumno veía «cloud Microsoft Azure» en la lista de
    rutas. Un emoji o una sigla corta en mayúsculas («JS») sí se ven bien.
    """
    import re

    as_text = [
        f"{t['id']}: {t.get('icon')!r}"
        for t in _tracks()
        if not t.get("icon") or re.fullmatch(r"[a-z][a-z0-9-]*", t["icon"])
    ]
    assert not as_text, f"icons that would render as a plain word: {as_text}"
