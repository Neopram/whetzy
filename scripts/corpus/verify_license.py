"""Lee la licencia de una fuente descargada y decide si se puede reutilizar.

Reglas (ADR-11, ADR-43):
* **Se acepta** para reutilizar: MIT, Apache-2.0, BSD, PSF-2.0, CC BY, CC0,
  Unlicense y dominio público (incluido Project Gutenberg en EE. UU.).
* **Se rechaza** con motivo: NonCommercial (CC BY-NC), ShareAlike (CC BY-SA,
  ADR-43 «no»), GPL/LGPL/AGPL (copyleft: se cita, no se copia), propietario, y
  cualquier fuente **sin fichero de licencia ni marca reconocible**.

La licencia que manda es el fichero del commit descargado, no la tabla del
catálogo (CATALOGO_MAESTRO.md §2.2, regla 2). Si no se puede leer, no entra.

    python -m scripts.corpus.verify_license --name thealgorithms-python
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from scripts.corpus.common import CORPUS, now_iso, source_dir, write_meta

LICENSE_FILES = re.compile(r"^(LICEN[CS]E|COPYING|UNLICENSE)(\.(md|txt|rst))?$", re.IGNORECASE)
HEADER_BYTES = 40_000

# Licencias cuyo texto **menciona** una licencia rechazable sin serlo: la PSF
# dice «GPL-compatible doesn't mean that we're distributing Python under the
# GPL». Se reconocen primero, por su título completo, y solo ellas.
PRIORITY_ACCEPT = [
    (re.compile(r"PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2", re.IGNORECASE), "PSF-2.0"),
]
# Orden importa: lo que rechaza se mira antes que lo que acepta, porque un texto
# CC BY-NC-SA contiene también «Creative Commons Attribution».
REJECT = [
    (re.compile(r"non-?commercial|\bCC[- ]BY[- ]NC\b", re.IGNORECASE), "NonCommercial (CC BY-NC): se cita, no se reutiliza (ADR-11)"),
    (re.compile(r"share-?alike|\bCC[- ]BY[- ]SA\b", re.IGNORECASE), "ShareAlike (CC BY-SA): no se reutiliza (ADR-43, H.LIC = no)"),
    (re.compile(r"GNU (AFFERO |LESSER )?GENERAL PUBLIC LICENSE|\bA?L?GPL-?\d", re.IGNORECASE), "copyleft GPL/LGPL/AGPL: se cita, no se copia (ADR-11)"),
    (re.compile(r"all rights reserved", re.IGNORECASE), "propietario («All rights reserved»)"),
]
ACCEPT = [
    (re.compile(r"Apache License,?\s+Version 2\.0", re.IGNORECASE), "Apache-2.0"),
    (re.compile(r"Permission is hereby granted, free of charge", re.IGNORECASE), "MIT"),
    (re.compile(r"Redistribution and use in source and binary forms", re.IGNORECASE), "BSD"),
    (re.compile(r"CC0|Creative Commons Zero", re.IGNORECASE), "CC0-1.0"),
    (re.compile(r"This is free and unencumbered software released into the public domain", re.IGNORECASE), "Unlicense"),
    (re.compile(r"Creative Commons Attribution \d\.\d|\bCC[- ]BY[- ]\d\.\d", re.IGNORECASE), "CC-BY"),
    (re.compile(r"Project Gutenberg(?:\u2122)? License.*public domain in the United\s+States", re.IGNORECASE | re.DOTALL), "PD-US (Project Gutenberg)"),
]


@dataclass(frozen=True)
class Verdict:
    accepted: bool
    spdx: str | None
    reason: str
    evidence: str | None


def _license_text(raw: Path) -> tuple[str | None, str | None]:
    """(texto, fichero) del fichero de licencia en la raíz, o la cabecera de un
    fichero suelto (fuentes `http`, p. ej. un libro de Gutenberg)."""
    if not raw.exists():
        return None, None
    for f in sorted(raw.iterdir()):
        if f.is_file() and LICENSE_FILES.match(f.name):
            return f.read_text(encoding="utf-8", errors="replace"), f.name
    files = [f for f in raw.iterdir() if f.is_file()]
    if len(files) == 1:
        # Cabecera y pie: Gutenberg declara la licencia al final del libro.
        data = files[0].read_bytes()
        text = (data[:HEADER_BYTES] + b"\n" + data[-HEADER_BYTES:]).decode("utf-8", errors="replace")
        m = re.search(r"SPDX-License-Identifier:\s*([\w.\-+]+)", text)
        return (m.group(0) if m else text), f"{files[0].name} (cabecera y pie)"
    return None, None


def classify(text: str | None, where: str | None = None) -> Verdict:
    if not text:
        return Verdict(False, None, "sin fichero LICENSE/COPYING ni marca de licencia: rechazada (ADR-42)", None)
    for rx, spdx in PRIORITY_ACCEPT:
        m = rx.search(text)
        if m:
            return Verdict(True, spdx, "licencia reutilizable (ADR-11)", m.group(0)[:120])
    for rx, reason in REJECT:
        m = rx.search(text)
        if m:
            return Verdict(False, None, reason, m.group(0))
    for rx, spdx in ACCEPT:
        m = rx.search(text)
        if m:
            return Verdict(True, spdx, "licencia reutilizable (ADR-11)", m.group(0)[:120])
    if where and where.endswith("(cabecera y pie)"):
        return Verdict(False, None, "sin fichero LICENSE ni marca de licencia en cabecera o pie: rechazada (ADR-42)", None)
    return Verdict(False, None, "licencia no reconocida: rechazada hasta leerla a mano", None)


def verify(src: Path) -> Verdict:
    text, where = _license_text(src / "raw")
    v = classify(text, where)
    write_meta(src, license_checked_at=now_iso(), license_file=where, accepted=v.accepted,
               spdx=v.spdx, license_reason=v.reason, license_evidence=v.evidence)
    return v


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name", required=True)
    ap.add_argument("--corpus", type=Path, default=CORPUS)
    a = ap.parse_args(argv)
    v = verify(source_dir(a.name, a.corpus))
    mark = "ACEPTADA" if v.accepted else "RECHAZADA"
    print(f"[licencia] {a.name}: {mark} — {v.spdx or '-'} — {v.reason}")
    return 0 if v.accepted else 3


if __name__ == "__main__":
    sys.exit(main())
