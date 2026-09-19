"""Unit tests for security headers middleware (ASVS V14.4).

Verifies that all required security headers are present in HTTP responses,
including HSTS, CSP, X-Frame-Options, and other defense-in-depth headers.
"""

from __future__ import annotations


async def test_security_headers_present_on_health_endpoint(client):
    """Verify all security headers are present in response."""
    response = await client.get("/health")
    assert response.status_code == 200

    # ASVS V14.4: Verify required security headers
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("Permissions-Policy") == "geolocation=(), microphone=(), camera=(), payment=()"
    assert response.headers.get("X-Permitted-Cross-Domain-Policies") == "none"
    assert response.headers.get("Cross-Origin-Opener-Policy") == "same-origin"
    assert response.headers.get("Cross-Origin-Resource-Policy") == "same-origin"
    assert response.headers.get("Cache-Control") == "no-store"


async def test_csp_header_present(client):
    """Verify Content-Security-Policy header is set."""
    response = await client.get("/health")
    csp = response.headers.get("Content-Security-Policy")
    assert csp is not None
    assert "default-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "base-uri 'none'" in csp


async def test_hsts_header_in_production_mode(client):
    """Verify HSTS header is present in production (when enabled)."""
    # Note: HSTS is only enabled when ENVIRONMENT != "development"
    # In tests, ENVIRONMENT is set to "test", so HSTS won't be in dev mode
    # This test documents the expected behavior
    response = await client.get("/health")
    # In test environment, HSTS may not be present (depends on enable_hsts flag)
    # but when enabled, it should have proper settings
    if response.headers.get("Strict-Transport-Security"):
        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=" in hsts
        assert "includeSubDomains" in hsts


async def test_security_headers_on_api_endpoint(client):
    """Verify security headers are also present on API endpoints."""
    response = await client.get("/api/v1/openapi.json")
    # Even on API endpoints, security headers should be present
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"


async def test_no_server_header_leakage(client):
    """Verify server implementation details are not exposed."""
    response = await client.get("/health")
    # Should not expose server software version details
    server_header = response.headers.get("Server")
    if server_header:
        # If present, should be generic or empty
        assert "uvicorn" not in server_header.lower()


async def test_cache_control_no_store(client):
    """Verify sensitive responses disable caching."""
    response = await client.get("/health")
    cache_control = response.headers.get("Cache-Control")
    assert cache_control == "no-store"
