"""La configuración de Cloudflare Pages que vive en el repo (ledger 30.3).

El incidente de login del 2026-09-24 tuvo tres piezas y ninguna era código de
la app: un `functions/` en la raíz, un `frontend/functions/api/[[path]].js`
que respondía 200 «Autenticado correctamente» a cualquier POST, y una URL de API
equivocada. A eso se suma que sin `package-lock.json` el job e2e de CI muere
antes de correr (34.10). Nada de eso lo ve un test de la app; esto sí.

Las reglas de la URL son las de `requireApiUrl` en `frontend/vite.config.ts`.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parents[2]
FRONTEND = RAIZ / "frontend"
FUNCION_API = FRONTEND / "functions" / "api" / "[[path]].js"
DOMINIO_FRONTEND = "whetzy.com"


def test_no_hay_functions_en_la_raiz() -> None:
    # Pages toma `functions/` del directorio del proyecto; uno en la raíz del
    # repo es el que servía el falso «Autenticado correctamente».
    assert not (RAIZ / "functions").exists(), "functions/ en la raíz del repo: bórralo"


def test_la_funcion_de_api_solo_responde_404() -> None:
    assert FUNCION_API.is_file(), f"falta {FUNCION_API.relative_to(RAIZ)}"
    fuente = FUNCION_API.read_text(encoding="utf-8")
    estados = re.findall(r"status:\s*(\d{3})", fuente)
    assert estados == ["404"], f"/api/* en el frontend debe ser solo 404; hay {estados}"


def test_la_api_de_produccion_no_es_el_frontend() -> None:
    env = (FRONTEND / ".env.production").read_text(encoding="utf-8")
    m = re.search(r"^VITE_API_URL=(\S+)$", env, re.MULTILINE)
    assert m, "frontend/.env.production sin VITE_API_URL"
    url = urlparse(m.group(1))
    assert url.scheme == "https", m.group(1)
    assert url.hostname and not url.hostname.endswith(DOMINIO_FRONTEND), (
        f"{m.group(1)} es el propio frontend: el login daría 405"
    )
    assert url.path.rstrip("/").endswith("/api/v1"), f"{m.group(1)} no acaba en /api/v1"


def test_hay_package_lock() -> None:
    assert (FRONTEND / "package-lock.json").is_file(), "sin package-lock.json, CI no instala"
