"""Ninguna pregunta nueva puede ser casi-duplicada de otra del mismo track (39.7).

La lógica vive en `scripts/check_originality.py`; aquí solo se exige que no
haya parejas fuera de la deuda anotada el 2026-09-26.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "check_originality.py"
_spec = importlib.util.spec_from_file_location("check_originality", _SCRIPT)
assert _spec and _spec.loader
check_originality = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_originality)


def test_no_new_near_duplicate_questions() -> None:
    fresh = check_originality.new_pairs(check_originality.pairs())
    assert not fresh, f"casi-duplicadas nuevas: {fresh[:10]}"
