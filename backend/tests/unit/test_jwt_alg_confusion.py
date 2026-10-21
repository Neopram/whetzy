"""PYSEC-2026-4298 (python-jose ≤ 3.5.0, sin versión arreglada): con una clave
pública DER, python-jose deja firmar HS256 con ella y la verificación lo acepta
si el servicio no restringe los algoritmos. Aquí nunca se llega:

- la clave pública solo se usa con `["RS256"]` y el secreto HS256 es
  `SECRET_KEY`, no una clave pública (`_verification_keys`);
- Apple se verifica solo con `["RS256"]` (`apple_signin.py`).

Estos tests vigilan las dos cosas; con ellos en verde, `pip-audit` ignora el
aviso en el CI hasta que python-jose publique arreglo o se cambie de librería.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from app.core.security import _verification_keys, verify_token

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PRIVATE_PEM = _KEY.private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
).decode()
PUBLIC_PEM = _KEY.public_key().public_bytes(
    serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
).decode()
PUBLIC_DER = _KEY.public_key().public_bytes(
    serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
)

HMAC_ALGS = {"HS256", "HS384", "HS512"}


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _forge_hs256(secret: bytes) -> str:
    """Un token HS256 firmado a mano con `secret`, como haría el atacante."""
    now = datetime.now(UTC)
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    claims = {
        "sub": str(uuid4()),
        "type": "access",
        "jv": 1,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
    }
    body = _b64(json.dumps(claims).encode())
    sig = hmac.new(secret, f"{header}.{body}".encode(), hashlib.sha256).digest()
    return f"{header}.{body}.{_b64(sig)}"


def test_la_clave_publica_nunca_va_con_un_algoritmo_hmac():
    with patch.multiple("app.core.security.settings", JWT_PRIVATE_KEY=PRIVATE_PEM, JWT_PUBLIC_KEY=PUBLIC_PEM):
        for key, algorithms in _verification_keys():
            if key == PUBLIC_PEM:
                assert not HMAC_ALGS & set(algorithms), algorithms


@pytest.mark.parametrize("secret", [PUBLIC_PEM.encode(), PUBLIC_DER], ids=["pem", "der"])
def test_hs256_firmado_con_la_clave_publica_se_rechaza(secret: bytes):
    with patch.multiple("app.core.security.settings", JWT_PRIVATE_KEY=PRIVATE_PEM, JWT_PUBLIC_KEY=PUBLIC_PEM):
        with pytest.raises(HTTPException) as exc:
            verify_token(_forge_hs256(secret), expected_type="access")
        assert exc.value.status_code == 401


def test_apple_solo_acepta_rs256():
    src = (Path(__file__).resolve().parents[2] / "app" / "services" / "apple_signin.py").read_text()
    assert 'algorithms=["RS256"]' in src
