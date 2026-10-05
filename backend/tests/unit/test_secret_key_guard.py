"""En producción, el arranque falla con una SECRET_KEY de ejemplo o corta (S.16).

`verify_token` acepta HS256 con `SECRET_KEY` aunque haya clave RS256, así que
una clave conocida en producción deja firmar la sesión de cualquier alumno.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import _DEV_SECRET_KEY, SECRET_KEY_MIN_LENGTH, Settings

STRONG = "0123456789abcdef" * 4  # 64 caracteres, como `secrets.token_hex(32)`


@pytest.mark.parametrize(
    "key",
    [
        _DEV_SECRET_KEY,
        "change-me-to-a-64-char-random-hex-string",  # el de .env.example
        f"  {_DEV_SECRET_KEY}\n",  # pegado con espacios en Railway
        "x" * (SECRET_KEY_MIN_LENGTH - 1),
        "",
    ],
)
def test_produccion_no_arranca_con_una_clave_de_ejemplo_o_corta(key: str) -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, ENVIRONMENT="production", SECRET_KEY=key)


def test_produccion_arranca_con_una_clave_propia() -> None:
    settings = Settings(_env_file=None, ENVIRONMENT="production", SECRET_KEY=STRONG)
    assert settings.SECRET_KEY == STRONG


@pytest.mark.parametrize("environment", ["development", "staging", "test"])
def test_fuera_de_produccion_la_clave_de_desarrollo_vale(environment: str) -> None:
    settings = Settings(_env_file=None, ENVIRONMENT=environment, SECRET_KEY=_DEV_SECRET_KEY)
    assert settings.SECRET_KEY == _DEV_SECRET_KEY
