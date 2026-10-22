"""Contrato puerto ↔ CORS de la suite e2e (42.2).

`frontend/playwright.config.ts` levanta el frontend en unos puertos (`--port NNNN`
en `webServer`) y le pasa al backend su lista de orígenes (`BACKEND_CORS_ORIGINS`).
Si un puerto no está en la lista, el middleware CSRF rechaza todo POST con cookie
de sesión que salga de él: el 2026-10-16, 18 de 52 specs en rojo por el :5199.
"""

from __future__ import annotations

import re
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[2] / "frontend" / "playwright.config.ts"


def _texto() -> str:
    return CONFIG.read_text(encoding="utf-8")


def _puertos_frontend() -> list[str]:
    # Solo los `npm run dev -- --port NNNN`: el de uvicorn (8000) es el backend.
    puertos = re.findall(r"command:\s*'npm run dev[^']*--port (\d+)", _texto())
    assert puertos, f"no encuentro ningún `npm run dev -- --port NNNN` en {CONFIG}"
    return puertos


def _origenes_cors() -> list[str]:
    m = re.search(
        r"BACKEND_CORS_ORIGINS:\s*JSON\.stringify\(\[(.*?)\]\)", _texto(), re.DOTALL
    )
    assert m, f"no encuentro `BACKEND_CORS_ORIGINS: JSON.stringify([...])` en {CONFIG}"
    origenes = re.findall(r"'([^']+)'", m.group(1))
    assert origenes, "BACKEND_CORS_ORIGINS está vacía"
    return origenes


def test_cada_puerto_del_frontend_e2e_esta_en_cors() -> None:
    origenes = set(_origenes_cors())
    faltan = [p for p in _puertos_frontend() if f"http://localhost:{p}" not in origenes]
    assert not faltan, (
        f"puertos del frontend e2e sin su origen en BACKEND_CORS_ORIGINS: {faltan}. "
        f"Lista actual: {sorted(origenes)}"
    )


def test_la_guarda_ve_los_dos_frontends() -> None:
    """:5199 (mismo sitio) y :5198 (entre sitios, 43.1). Si la regex dejara de
    ver alguno, la guarda de arriba pasaría en vacío."""
    assert {"5199", "5198"} <= set(_puertos_frontend())
