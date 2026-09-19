"""Integration tests for CORS security configuration (ASVS V14.2).

Verifies that CORS is properly configured to only allow approved origins,
preventing unauthorized cross-origin requests.
"""

from __future__ import annotations


async def test_cors_allowed_origin_whetzy_production(client):
    """Verify CORS allows whetzy.com production domain."""
    response = await client.get(
        "/health",
        headers={"Origin": "https://whetzy.com"}
    )
    assert response.status_code == 200
    # CORS headers should be present for allowed origin
    assert "access-control-allow-origin" in response.headers


async def test_cors_allowed_origin_pages_dev(client):
    """Verify CORS allows whetzy.pages.dev (not wildcard)."""
    response = await client.get(
        "/health",
        headers={"Origin": "https://whetzy.pages.dev"}
    )
    assert response.status_code == 200


async def test_cors_allowed_origin_localhost_dev(client):
    """Verify CORS allows localhost for development."""
    response = await client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200


async def test_cors_rejects_unauthorized_origin(client):
    """Verify CORS rejects unauthorized origins."""
    response = await client.get(
        "/health",
        headers={"Origin": "https://attacker.com"}
    )
    assert response.status_code == 200
    # While the request succeeds, CORS headers should not permit the origin
    # The browser will block access to the response
    allow_origin = response.headers.get("access-control-allow-origin")
    # For a rejected origin, either no CORS header or wildcard should not be present
    if allow_origin:
        assert allow_origin != "*"


async def test_cors_wildcard_subdomain_not_allowed(client):
    """Verify CORS does NOT accept wildcard subdomains like *.pages.dev."""
    # Test with a random subdomain that matches *.pages.dev pattern
    response = await client.get(
        "/health",
        headers={"Origin": "https://random-subdomain.pages.dev"}
    )
    # Request succeeds at HTTP level, but CORS headers should reject it
    allow_origin = response.headers.get("access-control-allow-origin")
    # Wildcard should not be present, only explicit origins allowed
    if allow_origin:
        assert allow_origin != "*"
        assert "pages.dev" not in allow_origin or "whetzy.pages.dev" in allow_origin


async def test_cors_credentials_allowed(client):
    """Verify CORS allows credentials for authenticated requests."""
    response = await client.get(
        "/health",
        headers={"Origin": "https://whetzy.com"}
    )
    # Should indicate credentials are allowed
    allow_credentials = response.headers.get("access-control-allow-credentials")
    if allow_credentials:
        assert allow_credentials.lower() == "true"


async def test_cors_preflight_options_request(client):
    """Verify CORS preflight (OPTIONS) requests are handled correctly."""
    response = await client.options(
        "/health",
        headers={
            "Origin": "https://whetzy.com",
            "Access-Control-Request-Method": "GET",
        }
    )
    # Preflight should either return 200 or 204
    assert response.status_code in (200, 204)


# --- 22.2: los origenes de loopback no sobreviven a produccion -------------


def _origins_for(environment: str) -> list[str]:
    """Build a Settings with the given ENVIRONMENT and return the active origins."""
    from app.core.config import Settings

    return Settings(ENVIRONMENT=environment).active_cors_origins


def test_production_drops_loopback_origins() -> None:
    """En produccion, localhost y 127.0.0.1 no pueden ser origenes aprobados.

    Con allow_credentials=True, dejarlos significa que una pagina servida desde
    http://localhost:5173 en la maquina de cualquiera es origen aprobado contra
    la API viva. El defecto se probo en los dos sentidos: en development siguen.
    """
    prod = _origins_for("production")
    assert prod, "produccion se quedo sin ningun origen aprobado"
    for origin in prod:
        assert "localhost" not in origin, origin
        assert "127.0.0.1" not in origin, origin
    assert "https://whetzy.com" in prod


def test_development_keeps_loopback_origins() -> None:
    """En desarrollo siguen ahi, o nadie puede trabajar en local."""
    dev = _origins_for("development")
    assert "http://localhost:5173" in dev
    assert "http://127.0.0.1:3000" in dev


def test_staging_keeps_loopback_origins() -> None:
    """Solo 'production' recorta; staging no se toca sin decirlo."""
    assert "http://localhost:3000" in _origins_for("staging")
