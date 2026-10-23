"""H.50: el script de sesión en la nube descarga todo repo git del índice y nada más.

Lo que cuenta es el criterio: cada fuente de `content/sources/index.json` que es un
repo de GitHub entra en el plan, y las webs se listan como omitidas. Si alguien cambia
el filtro, este test sale en rojo.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "corpus" / "sesion_nube.sh"


def _dry_run() -> str:
    env = {**os.environ, "SESION_NUBE_DRY": "1"}
    out = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout


def test_el_script_es_ejecutable() -> None:
    assert os.access(SCRIPT, os.X_OK)


def test_plan_cubre_exactamente_los_repos_github_del_indice() -> None:
    fuentes = json.loads(
        (ROOT / "content" / "sources" / "index.json").read_text(encoding="utf-8")
    )
    git = {s["name"] for s in fuentes if s["url"].startswith("https://github.com/")}
    web = {s["name"] for s in fuentes if not s["url"].startswith("https://github.com/")}
    salida = _dry_run()
    planeados = {l.split()[1] for l in salida.splitlines() if l.startswith("[plan] ")}
    omitidos = {
        l.split()[1] for l in salida.splitlines() if l.startswith("[omitida-web] ")
    }
    assert planeados == git
    assert omitidos == web
    assert f"corpus: {len(git)} repos git" in salida
