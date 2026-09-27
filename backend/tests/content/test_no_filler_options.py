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
    # Segunda familia, encontrada el 2026-09-26 en tracks 18-23, 27 y 42 (39.28).
    "como concepto principal", "sin excepciones ni variantes",
    "de manera exclusiva y permanente",
    "as the main concept", "without exceptions or variants",
    "exclusively and permanently", "as the primary concept",
    # Tercera familia, medida el 2026-09-26 por la noche (39.28): cola de 2-6 palabras que
    # aparece en cientos de opciones incorrectas y en 0-2 correctas de todo el banco.
    "independientemente del contexto aplicado", "según la documentación estándar del servicio",
    "en cualquier escenario de implementación", "de forma invariable y constante",
    "sin considerar otros factores relevantes", "en todos los casos posibles",
    "de forma predeterminada", "como resultado", "en la mayoría de los casos", "en general",
    "en todos los escenarios",
    "regardless of the applied context", "according to standard service documentation",
    "in any implementation scenario", "invariably and constantly",
    "without considering other relevant factors", "in all possible cases", "as a result",
    "in most cases", "in general", "in all scenarios",
)

# Medido el 2026-09-26 tras reescribir track26, 28, 29 y 30 (0) y añadir la segunda familia
# de coletillas (39.28); re-medido esa misma noche al añadir la tercera familia: las cifras
# suben porque la guarda ahora ve más, no porque el banco empeorara. Solo baja.
BASELINE = {
    "track03_python_advanced": 1,
    "track04_software_engineering": 8,
    "track05_software_architecture": 4,
    "track06_ai_fundamentals": 8,
    "track07_ai_engineering": 5,
    "track08_aws_cloud_practitioner": 1,
    "track12_sql": 3,
    "track13_cybersecurity": 4,
    "track14_frontend": 232,
    "track16_algoritmos": 1,
    "track18_docker_k8s": 964,
    "track19_iac_cicd": 761,
    "track21_data_science": 776,
    "track22_azure": 430,
    "track23_gcp": 773,
    "track27_nosql": 566,
    "track44_azure_fundamentals": 106,
    "track45_azure_ai": 97,
    "track46_azure_data": 135,
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
