"""Huellas de generador en el contenido vivo no crecen (ledger 39.6).

El detalle y el porqué están en `scripts/audit_ai_traces.py`.
"""

from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location(
    "audit_ai_traces", ROOT / "scripts" / "audit_ai_traces.py"
)
assert _spec and _spec.loader
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)


def test_the_detector_sees_each_trace(tmp_path: Path) -> None:
    good = {
        "id": "q1",
        "explanation_es": "Porque la clave primaria es única.",
        "explanation_en": "Because the primary key is unique.",
    }
    cases = {
        "explicacion_plantilla": {
            "id": "q2",
            "explanation_es": "Explicación no disponible.",
            "explanation_en": "Because.",
        },
        "marcado_de_herramienta": {
            "id": "q3",
            "explanation_es": "Texto </invoke> filtrado",
            "explanation_en": "Leaked text",
        },
        "voz_de_asistente": {
            "id": "q4",
            "explanation_es": "Aquí tienes la respuesta.",
            "explanation_en": "Fine.",
        },
    }
    for kind, q in cases.items():
        f = tmp_path / f"{kind}.json"
        f.write_text(json.dumps({"questions": [good, q]}), encoding="utf-8")
        found = audit.traces([f])
        counts = next(iter(found.values()), Counter())
        assert counts[kind] >= 1, kind


def test_a_real_explanation_is_not_a_trace(tmp_path: Path) -> None:
    f = tmp_path / "ok.json"
    f.write_text(
        json.dumps(
            {
                "questions": [
                    {
                        "id": "q1",
                        "explanation_es": "Correcto: el índice evita el recorrido completo.",
                        "explanation_en": "Right: the index avoids a full scan.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert audit.traces([f]) == {}


def test_live_content_never_adds_traces() -> None:
    base = json.loads(audit.BASELINE.read_text(encoding="utf-8"))
    bad = audit.regressions(audit.traces(), base)
    assert not bad, f"{len(bad)} ficheros con más huellas que su línea base: {bad[:10]}"
