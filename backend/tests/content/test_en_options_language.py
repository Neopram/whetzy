"""English options written in Spanish (39.36).

The generator of tracks 21 and 44-46 translated only the filler ending of each
option, so learners studying in English saw "Imputar con la media o mediana..."
or "Nube Híbrida" as answers. Found on 2026-09-27 while rewriting 39.28.

The check is a heuristic (Spanish accents, ¿/¡, or common Spanish function
words) and counts questions, not options. A handful of hits outside those
tracks are legitimate (code identifiers such as ``módulo``, a surname, Ctrl+Alt+Del),
so ``BASELINE`` is a ratchet measured on 2026-09-27: a track may go down, never up.
"""

from __future__ import annotations

import json
import re
from collections import Counter

from app.services.content_loader import _content_root

SPANISH = re.compile(
    r"[áéíóúñ¿¡]|\b(de|del|con|los|las|para|una|sin|según|cuando|datos|solo|entre)\b",
    re.IGNORECASE,
)

BASELINE = {
    "track02_python_intermediate": 1,
    "track03_python_advanced": 1,
    "track04_software_engineering": 2,
    "track13_cybersecurity": 1,
    "track21_data_science": 194,
    "track29_qa_testing": 1,
    "track40_isc2_cc": 1,
    "track41_pcap": 2,
    "track44_azure_fundamentals": 46,
    "track45_azure_ai": 33,
    "track46_azure_data": 49,
}


def spanish_en_option_counts() -> Counter[str]:
    counts: Counter[str] = Counter()
    root = _content_root() / "questions"
    for qfile in sorted(root.rglob("*.json")):
        track = qfile.relative_to(root).parts[0]
        payload = json.loads(qfile.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else payload.get("questions", [])
        for q in items:
            if any(SPANISH.search(str(o)) for o in q.get("options_en") or []):
                counts[track] += 1
    return counts


def test_english_options_in_spanish_never_grow() -> None:
    counts = spanish_en_option_counts()
    worse = {t: (n, BASELINE.get(t, 0)) for t, n in counts.items() if n > BASELINE.get(t, 0)}
    assert not worse, f"options_en in Spanish grew (now, allowed): {worse}"
