"""Sign in with Apple, lado servidor (19.2, ADR-13). Preparado, no verificado: H.2.

Sin el Apple Developer Program no hay Services ID ni clave, así que nada de esto
se ha probado contra Apple: los tests firman con claves propias. Lo que sigue
sale de la documentación de Apple leída el 2026-10-20 (en JSON, porque la web la
pinta con JavaScript): ``developer.apple.com/tutorials/data/documentation/``

- ``accountorganizationaldatasharing/creating-a-client-secret.json``: el
  ``client_secret`` es un JWT ES256 con ``kid`` (Key ID), ``iss`` (Team ID),
  ``iat``, ``exp`` (como mucho 15.777.000 s después), ``aud``
  ``https://appleid.apple.com`` y ``sub`` (el mismo ``client_id``), firmado con
  la clave ``.p8`` de la cuenta.
- ``signinwithapple/incorporating-sign-in-with-apple-into-other-platforms.json``:
  si se piden ``name``/``email``, ``response_mode`` tiene que ser ``form_post``
  (Apple vuelve con un ``POST`` de formulario); se puede mandar ``nonce``.
- ``signinwithapple/verifying-a-user.json``: el ``id_token`` se verifica con la
  clave pública del servidor, el ``nonce``, ``iss`` = ``https://appleid.apple.com``,
  ``aud`` = ``client_id`` y ``exp``.

La URL de las claves públicas (``/auth/keys``) y la de tokens (``/auth/token``)
son las de la API REST de Apple [Likely: no aparecen en esas tres páginas].
"""
from __future__ import annotations

import hashlib
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings

ISSUER = "https://appleid.apple.com"
AUTH_URL = "https://appleid.apple.com/auth/authorize"
TOKEN_URL = "https://appleid.apple.com/auth/token"
KEYS_URL = "https://appleid.apple.com/auth/keys"
# Seis meses es el máximo; una hora basta para un intercambio de código.
CLIENT_SECRET_TTL_S = 3600


def configured() -> bool:
    """Las cuatro variables o ninguna: con una a medias, el botón no sale."""
    return all(
        (settings.APPLE_CLIENT_ID, settings.APPLE_TEAM_ID, settings.APPLE_KEY_ID, settings.APPLE_PRIVATE_KEY)
    )


def client_secret(now: int) -> str:
    return jwt.encode(
        {
            "iss": settings.APPLE_TEAM_ID,
            "iat": now,
            "exp": now + CLIENT_SECRET_TTL_S,
            "aud": ISSUER,
            "sub": settings.APPLE_CLIENT_ID,
        },
        # Railway guarda la clave en una sola línea: los saltos van como «\n».
        settings.APPLE_PRIVATE_KEY.replace("\\n", "\n"),
        algorithm="ES256",
        headers={"kid": settings.APPLE_KEY_ID},
    )


def nonce_for(code_verifier: str) -> str:
    """El ``nonce`` sale del ``code_verifier`` que /start ya guarda en
    ``oauth_states``: único por intento, secreto y sin columna nueva."""
    return hashlib.sha256(f"apple-nonce:{code_verifier}".encode()).hexdigest()


class InvalidAppleToken(Exception):
    """El ``id_token`` no pasa alguna comprobación: no se abre sesión."""


def verify_id_token(id_token: str, keys: dict[str, Any], nonce: str | None) -> dict[str, Any]:
    try:
        claims: dict[str, Any] = jwt.decode(
            id_token,
            keys,
            algorithms=["RS256"],
            audience=settings.APPLE_CLIENT_ID,
            issuer=ISSUER,
        )
    except JWTError as exc:
        raise InvalidAppleToken(str(exc)) from exc
    if nonce is not None and claims.get("nonce") != nonce:
        raise InvalidAppleToken("nonce")
    if not claims.get("sub"):
        raise InvalidAppleToken("sub")
    return claims


def verified_email(claims: dict[str, Any]) -> str | None:
    """Apple manda ``email_verified`` como booleano o como la cadena ``"true"``
    según la versión [Likely]; las direcciones de reenvío privado
    (``is_private_email``) también llegan verificadas y valen igual."""
    if claims.get("email_verified") in (True, "true"):
        email = claims.get("email")
        return email if isinstance(email, str) and email else None
    return None
