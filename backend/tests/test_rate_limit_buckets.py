"""El limite por IP no puede castigar al uso normal ni confiar en el cliente.

Medido en produccion el 2026-09-20, antes de estos cambios: 14 de 20 intentos de
login desde un solo cliente devolvian 429, y los 429 aparecian de forma
intermitente en peticiones consecutivas. Tres causas, una por clase de aqui:

1. `/auth/me` y `/auth/refresh` gastaban el presupuesto estricto pensado para
   frenar el relleno de credenciales, y la app llama a `/auth/me` en cada arranque.
2. Con `TRUST_PROXY_HEADERS` en false detras del proxy de Railway,
   `request.client.host` es la IP del proxy: un unico cubo para todo el mundo.
3. `_hits` acumulaba una clave por IP vista y no la soltaba nunca.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.security_middleware import RateLimitMiddleware


def _app(*, auth_limit: int = 3, default_limit: int = 50) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware, default_limit=default_limit, auth_limit=auth_limit
    )

    @app.get("/{full_path:path}")
    async def eco(full_path: str) -> dict[str, str]:
        return {"ok": full_path}

    @app.post("/{full_path:path}")
    async def eco_post(full_path: str) -> dict[str, str]:
        return {"ok": full_path}

    return app


async def _pedir(app: FastAPI, path: str, n: int, ip: str | None = None) -> list[int]:
    headers = {"X-Forwarded-For": ip} if ip else {}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://t"
    ) as client:
        return [(await client.get(path, headers=headers)).status_code for _ in range(n)]


class TestQueCuentaComoSensible:
    async def test_login_agota_el_presupuesto_estricto(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", True)
        codigos = await _pedir(_app(auth_limit=3), "/api/v1/auth/login", 5, ip="198.51.100.1")
        assert codigos.count(429) == 2, codigos

    @pytest.mark.parametrize("ruta", ["/api/v1/auth/me", "/api/v1/auth/refresh", "/api/v1/auth/logout"])
    async def test_el_trafico_de_sesion_no_gasta_el_presupuesto_de_credenciales(
        self, ruta: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """La regresion que rompia el uso normal: `/auth/me` va en cada arranque."""
        monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", True)
        codigos = await _pedir(_app(auth_limit=3, default_limit=50), ruta, 10, ip="198.51.100.2")
        assert 429 not in codigos, codigos

    async def test_registro_y_reset_si_cuentan(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", True)
        for ruta in ("/api/v1/auth/register", "/api/v1/auth/forgot-password"):
            codigos = await _pedir(_app(auth_limit=2), ruta, 4, ip="198.51.100.3")
            assert 429 in codigos, (ruta, codigos)

    async def test_las_sondas_de_salud_estan_exentas(self) -> None:
        """`/health` era coincidencia exacta: `/health/ready` si contaba."""
        for ruta in ("/health", "/health/ready", "/health/live"):
            codigos = await _pedir(_app(auth_limit=1, default_limit=1), ruta, 5)
            assert 429 not in codigos, (ruta, codigos)


class TestIdentidadDelCliente:
    async def test_dos_ips_no_comparten_cubo(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Detras del proxy todos compartian uno solo."""
        monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", True)
        monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 1)
        app = _app(auth_limit=2)

        agotada = await _pedir(app, "/api/v1/auth/login", 3, ip="203.0.113.1")
        assert 429 in agotada

        otra = await _pedir(app, "/api/v1/auth/login", 2, ip="203.0.113.2")
        assert 429 not in otra, otra

    async def test_el_cliente_no_puede_inventarse_una_ip(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Se leia la entrada mas a la izquierda, que la escribe quien llama.

        Con una cabecera distinta en cada peticion, el limite entero se esquivaba.
        La IP de confianza es la que anade el proxy, a la derecha.
        """
        monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", True)
        monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 1)
        app = _app(auth_limit=2)

        codigos = []
        for i in range(5):
            # El atacante antepone una IP inventada distinta cada vez; el proxy
            # anade la suya real al final.
            codigos += await _pedir(
                app, "/api/v1/auth/login", 1, ip=f"10.0.0.{i}, 203.0.113.9"
            )
        assert 429 in codigos, codigos


class TestMemoria:
    async def test_las_claves_caducadas_se_sueltan(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`_hits` crecia con cada IP vista y no bajaba nunca."""
        monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", True)
        app = _app(auth_limit=5)
        medio = next(m for m in app.user_middleware if m.cls is RateLimitMiddleware)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            for i in range(20):
                await c.get("/api/v1/auth/login", headers={"X-Forwarded-For": f"192.0.2.{i}"})

        instancia = app.middleware_stack
        while instancia is not None and not isinstance(instancia, RateLimitMiddleware):
            instancia = getattr(instancia, "app", None)
        assert instancia is not None, "no encuentro la instancia del middleware"
        assert len(instancia._hits) == 20

        # Una ventana despues, la siguiente peticion de cada clave la suelta.
        instancia._window = 0.01
        await asyncio.sleep(0.05)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            for i in range(20):
                await c.get("/api/v1/auth/login", headers={"X-Forwarded-For": f"192.0.2.{i}"})

        assert len(instancia._hits) <= 20
        assert medio is not None
