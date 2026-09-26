"""Wrong options padded with a filler ending so they match the right one in length (39.1).

The length-bias guard (37.16) was satisfied in tracks 26/28/29/30 by appending
phrases like "en este contexto" or "in practice" to the wrong options: the
correct answer stopped being the longest, and the wrong ones stopped meaning
anything precise. The ending is also a new tell, because the correct option
never carries it.

Ratchet: ``BASELINE`` is the count per track measured on 2026-09-26. A track may
go down, never up; a track that reaches 0 is removed and must stay at 0.
"""

from __future__ import annotations

import json
from collections import Counter

from app.services.content_loader import _content_root

FILLERS = (
    "en este contexto", "de forma general", "según la documentación oficial",
    "en la práctica habitual", "como regla general", "en el caso más común",
    "para la mayoría de proyectos", "en entornos de producción", "de manera estándar",
    "como práctica recomendada", "dentro de este paradigma", "en condiciones normales",
    "de forma estándar", "según la especificación", "en la práctica", "habitualmente",
    "por convención", "en entornos reales",
    "in this context", "as a general rule", "according to official documentation",
    "in common practice", "as a general guideline", "in the most common case",
    "for most projects", "in production environments", "as a standard approach",
    "as a recommended practice", "within this paradigm", "under normal conditions",
    "by default", "according to spec", "in practice", "typically", "by convention",
    "in real environments",
)

# Medido el 2026-09-26 tras reescribir track26 (0). Solo baja.
BASELINE = {
    "track03_python_advanced": 1,
    "track04_software_engineering": 8,
    "track05_software_architecture": 4,
    "track06_ai_fundamentals": 8,
    "track07_ai_engineering": 3,
    "track08_aws_cloud_practitioner": 1,
    "track12_sql": 3,
    "track13_cybersecurity": 3,
    "track14_frontend": 110,
    "track16_algoritmos": 1,
    "track22_azure": 1,
    "track27_nosql": 3,
    "track28_backend": 464,
    "track29_qa_testing": 426,
    "track30_agile": 610,
    "track42_security_plus": 66,
    "track43_aws_mla": 23,
    "track44_azure_fundamentals": 34,
    "track45_azure_ai": 23,
    "track46_azure_data": 59,
}


def filler_counts() -> Counter[str]:
    counts: Counter[str] = Counter()
    root = _content_root() / "questions"
    for qfile in sorted(root.rglob("*.json")):
        track = qfile.relative_to(root).parts[0]
        payload = json.loads(qfile.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else payload.get("questions", [])
        for q in items:
            ci = q.get("correct_index")
            for key in ("options_es", "options_en"):
                for i, opt in enumerate(q.get(key) or []):
                    low = str(opt).lower().rstrip(". ")
                    if i != ci and low.endswith(FILLERS):
                        counts[track] += 1
    return counts


def test_filler_endings_never_grow() -> None:
    counts = filler_counts()
    worse = {t: (n, BASELINE.get(t, 0)) for t, n in counts.items() if n > BASELINE.get(t, 0)}
    assert not worse, f"filler endings grew (now, allowed): {worse}"
