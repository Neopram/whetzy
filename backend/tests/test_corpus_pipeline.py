"""Pipeline del corpus (ledger 37.3): licencia, limpieza e índice, sin red.

Cada caso monta una fuente falsa en `tmp_path` con la forma que deja
`fetch.py` (`<corpus>/<nombre>/raw/…`) y pasa por el resto del pipeline.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.corpus import clean, index, verify_license
from scripts.corpus.common import write_meta

MIT = "MIT License\n\nPermission is hereby granted, free of charge, to any person obtaining a copy"
PSF = ("PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2\n...\n(1) GPL-compatible doesn't mean that "
       "we're distributing Python under the GPL.")


def _source(tmp_path: Path, name: str, files: dict[str, str]) -> Path:
    src = tmp_path / name
    raw = src / "raw"
    raw.mkdir(parents=True)
    for rel, text in files.items():
        p = raw / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    write_meta(src, name=name, kind="git", url=f"https://github.com/x/{name}", sha="abc123")
    return src


@pytest.mark.parametrize(
    ("files", "accepted", "spdx_or_reason"),
    [
        ({"LICENSE": MIT, "a.py": "print(1)"}, True, "MIT"),
        ({"LICENSE": PSF, "doc.rst": "Tutorial"}, True, "PSF-2.0"),
        ({"LICENSE.md": "Apache License, Version 2.0"}, True, "Apache-2.0"),
        ({"a.py": "print(1)", "b.py": "print(2)"}, False, "sin fichero LICENSE"),
        ({"LICENSE": "Attribution-NonCommercial-ShareAlike 4.0 International"}, False, "NonCommercial"),
        ({"LICENSE": "Creative Commons Attribution-ShareAlike 4.0"}, False, "ShareAlike"),
        ({"COPYING": "GNU GENERAL PUBLIC LICENSE Version 3"}, False, "copyleft"),
        ({"LICENSE": "Copyright ACME. All rights reserved."}, False, "propietario"),
        ({"LICENSE": "Copyright (c) 2020 X. All rights reserved.\n\n" + MIT}, True, "MIT"),
        ({"LICENSE": "Copyright X. All rights reserved.\nAttribution-NonCommercial 4.0"}, False, "NonCommercial"),
        ({"LICENSE": "Do whatever, I guess"}, False, "no reconocida"),
    ],
)
def test_verify_license(tmp_path, files, accepted, spdx_or_reason) -> None:
    v = verify_license.verify(_source(tmp_path, "s", files))
    assert v.accepted is accepted
    assert spdx_or_reason in (v.spdx if accepted else v.reason)


def test_gutenberg_licencia_en_el_pie(tmp_path) -> None:
    book = ("The Project Gutenberg eBook of X\n*** START OF THE PROJECT GUTENBERG EBOOK X ***\n"
            "Chapter I\nText.\n*** END OF THE PROJECT GUTENBERG EBOOK X ***\n"
            + "x\n" * 30000
            + "the Project Gutenberg License ... works in the collection are in the public domain in the United\nStates")
    src = _source(tmp_path, "pg", {"pg1.txt": book})
    v = verify_license.verify(src)
    assert v.accepted and v.spdx == "PD-US (Project Gutenberg)"
    clean.clean(src, "corpus-pruebas")
    texts = [p.read_text(encoding="utf-8") for p in (src / "clean").glob("*.txt")]
    assert texts == ["Chapter I\nText."]  # sin cabecera ni pie de la marca


def test_clean_deduplica_y_rechaza_lo_no_aceptado(tmp_path) -> None:
    src = _source(tmp_path, "ok", {"LICENSE": MIT, "a.md": "Hola   mundo", "dir/b.md": "Hola mundo", "img.png": "x"})
    verify_license.verify(src)
    stats = clean.clean(src, "track01")
    assert stats == {"kept": 1, "duplicates": 1, "skipped": 2}  # LICENSE sin extensión e img.png se saltan
    bad = _source(tmp_path, "bad", {"a.md": "texto"})
    verify_license.verify(bad)
    with pytest.raises(PermissionError):
        clean.clean(bad, "track01")


def test_index_solo_acepta_licencias_verificadas_y_no_duplica(tmp_path) -> None:
    src = _source(tmp_path, "ok", {"LICENSE": MIT})
    verify_license.verify(src)
    entry = index.entry_for(json.loads((src / ".meta.json").read_text(encoding="utf-8")))
    assert entry["mark"] == "reusar" and entry["spdx"] == "MIT" and entry["sha"] == "abc123"
    new, what = index.upsert([], entry)
    again, what2 = index.upsert(new, {**entry, "sha": "def456"})
    assert (what, what2, len(again), again[0]["sha"]) == ("añadida", "actualizada", 1, "def456")
    bad = _source(tmp_path, "bad", {"a.md": "t"})
    verify_license.verify(bad)
    with pytest.raises(PermissionError):
        index.entry_for(json.loads((bad / ".meta.json").read_text(encoding="utf-8")))


def test_index_guarda_alias_de_publicacion(tmp_path) -> None:
    src = _source(tmp_path, "cp", {"LICENSE": PSF})
    verify_license.verify(src)
    meta = json.loads((src / ".meta.json").read_text(encoding="utf-8"))
    entry = index.entry_for(meta, ["https://docs.python.org/3/", "https://docs.python.org/3"])
    assert entry["aliases"] == ["https://docs.python.org/3"]

