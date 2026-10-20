"""La app nativa (Capacitor) es un origen aprobado, también en producción.

El WebView de Capacitor sirve la app desde ``<esquema>://<hostname>``. Con el
``hostname`` por defecto (``localhost``) el origen era ``https://localhost`` en
Android y ``capacitor://localhost`` en iOS, y producción los descarta a
propósito (22.2: ningún loopback con ``allow_credentials``). Medido el
2026-10-20 contra api.whetzy.com: preflight de ``/auth/login`` desde esos dos
orígenes, 400; el APK no podía iniciar sesión.

``frontend/capacitor.config.ts`` fija ``server.hostname`` en un subdominio
propio y aquí se comprueba el contrato: lo que dice ese fichero es lo que
aprueban CORS y el control de Origin (los dos leen ``active_cors_origins``).
"""

from __future__ import annotations

import re
from pathlib import Path

CAPACITOR = Path(__file__).resolve().parents[3] / "frontend" / "capacitor.config.ts"


def _cap(clave: str, defecto: str) -> str:
    m = re.search(rf"\b{clave}:\s*'([^']+)'", CAPACITOR.read_text(encoding="utf-8"))
    return m.group(1) if m else defecto


def _origenes_nativos() -> list[str]:
    host = _cap("hostname", "localhost")
    return [f"{_cap('androidScheme', 'https')}://{host}", f"{_cap('iosScheme', 'capacitor')}://{host}"]


def _origins_for(environment: str) -> list[str]:
    from app.core.config import Settings

    return Settings(ENVIRONMENT=environment, SECRET_KEY="k" * 64).active_cors_origins


def test_el_hostname_de_la_app_no_es_loopback() -> None:
    """Con «localhost» producción lo recortaría y el teléfono no entra."""
    for origen in _origenes_nativos():
        assert "localhost" not in origen and "127.0.0.1" not in origen, origen


def test_produccion_aprueba_los_dos_origenes_de_la_app() -> None:
    prod = _origins_for("production")
    for origen in _origenes_nativos():
        assert origen in prod, f"{origen} no está en los orígenes de producción"


async def test_preflight_del_login_desde_la_app(client) -> None:
    for origen in _origenes_nativos():
        r = await client.options(
            "/api/v1/auth/login",
            headers={"Origin": origen, "Access-Control-Request-Method": "POST"},
        )
        assert r.status_code == 200, (origen, r.status_code)
        assert r.headers.get("access-control-allow-origin") == origen
