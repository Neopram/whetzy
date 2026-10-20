"""OAuth 2.0 social login — GitHub, Google and Apple (redirect flow, no third-party JS SDK).

Flow:
  1. Browser → GET /auth/oauth/{provider}/start
     Backend stores a CSRF state nonce and redirects to the provider auth page.
  2. Provider → GET /auth/oauth/{provider}/callback?code=…&state=…
     Backend validates state, exchanges code for provider token, resolves email,
     finds or creates user, issues JWT pair and redirects to FRONTEND_BASE_URL
     with both tokens in HttpOnly cookies (`set_auth_cookies`), never in the URL.
  3. Frontend loads with the session cookie already set, like after a password login.

Apple (19.2) differs in two places: it returns with a form `POST` to
`/apple/callback` (`response_mode=form_post`, required when asking for the
email), and the identity comes from its signed `id_token`, checked against
Apple's public keys (`app/services/apple_signin.py`). Prepared, not verified
against Apple: needs H.2.
"""
from __future__ import annotations

import base64
import hashlib
import re
import secrets
import time
import urllib.parse
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.cookies import (
    OAUTH_LANG_COOKIE,
    OAUTH_STATE_COOKIE,
    clear_oauth_state_cookie,
    set_oauth_lang_cookie,
    set_oauth_state_cookie,
)
from app.core.db import get_db
from app.core.security import create_access_token, create_refresh_token
from app.models.oauth import OAuthAccount, OAuthState
from app.models.user import User
from app.services import account_deletion, apple_signin
from app.services.user_lookup import normalize_email, user_by_email, username_taken

router = APIRouter()

_STATE_TTL_MINUTES = 10


def _pkce_pair() -> tuple[str, str]:
    """RFC 7636: `code_verifier` de 43-128 caracteres y su `code_challenge`
    S256 derivado. `token_urlsafe(64)` da ~86 caracteres, dentro del rango."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


class _UnverifiedEmailConflict(Exception):
    """Ya hay una cuenta con este email, pero esa cuenta no lo ha verificado.

    El proveedor OAuth ha verificado que quien está iniciando sesión ahora
    es el dueño real de ese email (GitHub filtra por `verified`, Google por
    `email_verified`). Pero `email_verified=False` en la cuenta existente
    de Whetzy no prueba lo mismo: cualquiera pudo registrarse con ese email
    por contraseña sin confirmarlo nunca. Sin este chequeo, un atacante que
    se registrara antes con el email de otra persona (típicamente por
    contraseña, nunca lo verifica) terminaba recibiendo el inicio de sesión
    real de esa persona en cuanto esta usara "Continuar con Google/GitHub"
    — la cuenta ya existía, el email coincidía, y se enlazaba sin preguntar.
    """

# Provider configs — lambdas so we read settings lazily (allows override in tests)
_PROVIDERS: dict[str, dict[str, Any]] = {
    "github": {
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "user_url": "https://api.github.com/user",
        "emails_url": "https://api.github.com/user/emails",
        "scope": "user:email",
        "client_id": lambda: settings.GITHUB_CLIENT_ID,
        "client_secret": lambda: settings.GITHUB_CLIENT_SECRET,
    },
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "user_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope": "openid email profile",
        "client_id": lambda: settings.GOOGLE_CLIENT_ID,
        "client_secret": lambda: settings.GOOGLE_CLIENT_SECRET,
    },
    "apple": {
        "auth_url": apple_signin.AUTH_URL,
        "token_url": apple_signin.TOKEN_URL,
        "scope": "name email",
        # Vacío si falta alguna de las cuatro variables: sin botón ni /start.
        "client_id": lambda: settings.APPLE_CLIENT_ID if apple_signin.configured() else "",
        "client_secret": lambda: apple_signin.client_secret(int(time.time())),
    },
}


def _http_client() -> httpx.AsyncClient:
    """Un punto donde los tests cambian el transporte (Apple, sin red)."""
    return httpx.AsyncClient(timeout=10)

# Test provider: available only outside production for E2E testing
_TEST_PROVIDER: dict[str, Any] = {
    "scope": "test",
    "client_id": lambda: "test-client-id",
    "client_secret": lambda: "test-client-secret",
}


def _get_provider(name: str) -> dict[str, Any]:
    if name in _PROVIDERS:
        return _PROVIDERS[name]
    if name == "test" and settings.ENVIRONMENT != "production":
        return _TEST_PROVIDER
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown OAuth provider")


def _callback_uri(provider: str) -> str:
    base = settings.OAUTH_REDIRECT_BASE_URL.rstrip("/")
    return f"{base}{settings.API_V1_PREFIX}/auth/oauth/{provider}/callback"


@router.get("/providers")
async def oauth_providers(response: Response) -> dict[str, list[str]]:
    """Proveedores con credenciales configuradas en este servidor.

    El frontend pinta solo los botones que salen aquí: un «Continuar con
    Google» que responde 404 al pulsarlo es peor que ningún botón.
    """
    response.headers["Cache-Control"] = "public, max-age=3600"
    return {"providers": [name for name, cfg in _PROVIDERS.items() if cfg["client_id"]()]}


# --------------------------------------------------------------------------
# /start
# --------------------------------------------------------------------------

@router.get("/{provider}/start")
async def oauth_start(
    provider: str,
    lang: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    cfg = _get_provider(provider)

    if provider != "test" and not cfg["client_id"]():
        # 404, como un proveedor desconocido: en este servidor no existe. Era 503,
        # que Sentry reporta como error y avisaba por un enlace viejo o un bot.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{provider} login is not configured on this server",
        )

    state = secrets.token_urlsafe(32)
    code_verifier, code_challenge = _pkce_pair()
    db.add(
        OAuthState(
            state=state,
            provider=provider,
            code_verifier=code_verifier,
            expires_at=datetime.now(UTC) + timedelta(minutes=_STATE_TTL_MINUTES),
        )
    )
    await db.commit()

    if provider == "test":
        # Test provider: skip real redirect, go straight to our own callback
        callback = _callback_uri("test")
        redirect = RedirectResponse(
            url=f"{callback}?code=test-code&state={state}",
            status_code=302,
        )
        set_oauth_state_cookie(redirect, state, _STATE_TTL_MINUTES * 60)
        _remember_lang(redirect, lang)
        return redirect

    params: dict[str, str] = {
        "client_id": cfg["client_id"](),
        "redirect_uri": _callback_uri(provider),
        "scope": cfg["scope"],
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    if provider == "google":
        params["response_type"] = "code"
        params["access_type"] = "offline"
    apple = provider == "apple"
    if apple:
        # Apple no lista PKCE entre sus parámetros; el `nonce` (derivado del
        # verifier guardado) ata el `id_token` a este intento.
        del params["code_challenge"], params["code_challenge_method"]
        params["response_type"] = "code"
        params["response_mode"] = "form_post"
        params["nonce"] = apple_signin.nonce_for(code_verifier)

    # Apple pide los espacios del `scope` como %20 («scope=name%20email»); los
    # demás siguen como estaban.
    quote = urllib.parse.quote if apple else urllib.parse.quote_plus
    auth_url = cfg["auth_url"] + "?" + urllib.parse.urlencode(params, quote_via=quote)
    redirect = RedirectResponse(url=auth_url, status_code=302)
    set_oauth_state_cookie(redirect, state, _STATE_TTL_MINUTES * 60, cross_site_post=apple)
    _remember_lang(redirect, lang, cross_site_post=apple)
    return redirect


# --------------------------------------------------------------------------
# /callback
# --------------------------------------------------------------------------

@router.get("/{provider}/callback")
async def oauth_callback(
    request: Request,
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if provider == "apple":
        # Apple solo vuelve por POST (form_post); un GET aquí no viene de Apple.
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Use POST")
    return await _complete(request, provider, code, state, db)


@router.post("/apple/callback")
async def oauth_apple_callback(
    request: Request,
    state: str = Form(...),
    code: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """`form_post` de Apple: `code`, `state`, `id_token` y, la primera vez,
    `user` (nombre). Sin `code` (el usuario canceló: `error=user_cancelled_authorize`)
    se vuelve a la app. El `id_token` del formulario no se usa: el que vale es
    el que devuelve /auth/token al canjear el código, de servidor a servidor.
    Exento del control de Origin (csrf.py): lo protegen el `state` (cookie y
    BD), el `nonce` y la firma de Apple."""
    if not code:
        cancelled = RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/?oauth_error=cancelled", status_code=302)
        clear_oauth_state_cookie(cancelled)
        return cancelled
    return await _complete(request, "apple", code, state, db)


async def _complete(
    request: Request, provider: str, code: str, state: str, db: AsyncSession
) -> RedirectResponse:
    _get_provider(provider)  # validates name

    # 41.14: el `state` también tiene que venir en la cookie HttpOnly que puso
    # /start — sin esto, un `state` válido y sin consumir se aceptaba desde
    # cualquier navegador, no solo el que inició este login (CSRF de login:
    # el atacante completa su propio flujo OAuth y engaña a la víctima para
    # que visite ese callback con sesión abierta).
    if request.cookies.get(OAUTH_STATE_COOKIE) != state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    # Validate and consume state nonce (CSRF protection)
    result = await db.execute(select(OAuthState).where(OAuthState.state == state))
    oauth_state = result.scalar_one_or_none()

    if oauth_state is None or oauth_state.provider != provider:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    if oauth_state.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        await db.delete(oauth_state)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth state expired")

    code_verifier = oauth_state.code_verifier
    await db.delete(oauth_state)
    await db.commit()

    # Resolve email and provider user ID
    if provider == "test":
        email: str | None = f"oauth-{code}@example.com"
        provider_user_id = f"test-{code}"
    else:
        async with _http_client() as client:
            token_data = await _exchange_code(client, provider, code, code_verifier)
            identity: tuple[str | None, str] | None = None
            if provider == "apple":
                try:
                    identity = await _apple_identity(client, token_data, code_verifier)
                except apple_signin.InvalidAppleToken:
                    identity = None
            elif token_data.get("access_token"):
                identity = await _get_user_info(client, provider, token_data["access_token"])
            if identity is None:
                error_redirect = RedirectResponse(
                    url=f"{settings.FRONTEND_BASE_URL}/?oauth_error=provider_error",
                    status_code=302,
                )
                clear_oauth_state_cookie(error_redirect)
                return error_redirect
            email, provider_user_id = identity

    if not email:
        error_redirect = RedirectResponse(
            url=f"{settings.FRONTEND_BASE_URL}/?oauth_error=email_required",
            status_code=302,
        )
        clear_oauth_state_cookie(error_redirect)
        return error_redirect

    try:
        user = await _find_or_create_user(
            db, email, provider, provider_user_id,
            language=_valid_lang(request.cookies.get(OAUTH_LANG_COOKIE)),
        )
    except _UnverifiedEmailConflict:
        error_redirect = RedirectResponse(
            url=f"{settings.FRONTEND_BASE_URL}/?oauth_error=email_unverified",
            status_code=302,
        )
        clear_oauth_state_cookie(error_redirect)
        return error_redirect
    if not user.is_active and not await account_deletion.restore_if_pending(db, user):
        error_redirect = RedirectResponse(
            url=f"{settings.FRONTEND_BASE_URL}/?oauth_error=account_inactive",
            status_code=302,
        )
        clear_oauth_state_cookie(error_redirect)
        return error_redirect

    from app.core.cookies import set_auth_cookies, set_mfa_cookie
    from app.core.security import create_mfa_token, user_has_2fa

    if await user_has_2fa(user.id, db):
        # Con 2FA, OAuth tampoco abre sesión sin el código: el token del segundo
        # paso va en una cookie HttpOnly (nunca en la URL) y la app pide el código.
        mfa_redirect = RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/auth?mfa=1", status_code=302)
        set_mfa_cookie(mfa_redirect, create_mfa_token(user.id, jwt_version=user.jwt_version))
        clear_oauth_state_cookie(mfa_redirect)
        return mfa_redirect

    access_token = create_access_token(user.id, jwt_version=user.jwt_version)
    refresh_token = create_refresh_token(user.id, jwt_version=user.jwt_version)

    redirect = RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/", status_code=302)
    set_auth_cookies(redirect, access_token, refresh_token)
    clear_oauth_state_cookie(redirect)
    return redirect


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

async def _exchange_code(
    client: httpx.AsyncClient,
    provider: str,
    code: str,
    code_verifier: str | None,
) -> dict[str, Any]:
    cfg = _PROVIDERS[provider]
    data: dict[str, str] = {
        "client_id": cfg["client_id"](),
        "client_secret": cfg["client_secret"](),
        "code": code,
        "redirect_uri": _callback_uri(provider),
    }
    if provider in ("google", "apple"):
        data["grant_type"] = "authorization_code"
    if provider == "apple":
        # Apple no usa PKCE (ver /start): el verifier solo sirvió para el nonce.
        code_verifier = None
    # PKCE (41.14): el code_verifier generado en /start. None solo si la fila
    # de oauth_states quedó sin él (una en vuelo en el momento del deploy que
    # añadió la columna) — el proveedor no lo exige si /start no mandó
    # code_challenge, así que el intercambio sigue sin romperse.
    if code_verifier:
        data["code_verifier"] = code_verifier
    resp = await client.post(cfg["token_url"], data=data, headers={"Accept": "application/json"})
    resp.raise_for_status()
    return resp.json()  # type: ignore[no-any-return]


async def _get_user_info(
    client: httpx.AsyncClient,
    provider: str,
    provider_token: str,
) -> tuple[str | None, str]:
    cfg = _PROVIDERS[provider]
    headers = {"Authorization": f"Bearer {provider_token}"}
    resp = await client.get(cfg["user_url"], headers=headers)
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()

    provider_user_id = str(data.get("id") or data.get("sub", ""))

    if provider == "github":
        email: str | None = data.get("email") or None
        if not email and "emails_url" in cfg:
            # GitHub may hide primary email — fetch from emails endpoint
            emails_resp = await client.get(cfg["emails_url"], headers=headers)
            if emails_resp.is_success:
                for entry in emails_resp.json():
                    if entry.get("primary") and entry.get("verified"):
                        email = entry["email"]
                        break
        return email, provider_user_id

    # Google: email_verified is in the userinfo payload
    if not data.get("email_verified"):
        return None, provider_user_id
    return data.get("email"), provider_user_id


async def _apple_identity(
    client: httpx.AsyncClient, token_data: dict[str, Any], code_verifier: str | None
) -> tuple[str | None, str]:
    """Email verificado y `sub` del `id_token` que Apple devuelve al canjear el
    código, tras comprobar firma, `iss`, `aud`, `exp` y `nonce`."""
    id_token = token_data.get("id_token")
    if not isinstance(id_token, str) or not id_token:
        raise apple_signin.InvalidAppleToken("sin id_token")
    keys = await client.get(apple_signin.KEYS_URL)
    keys.raise_for_status()
    nonce = apple_signin.nonce_for(code_verifier) if code_verifier else None
    claims = apple_signin.verify_id_token(id_token, keys.json(), nonce)
    return apple_signin.verified_email(claims), str(claims["sub"])


def _valid_lang(lang: str | None) -> str | None:
    return lang if lang in ("es", "en") else None


def _remember_lang(response: RedirectResponse, lang: str | None, *, cross_site_post: bool = False) -> None:
    # 45.1 (ADR-66 E1): un `lang` no válido se ignora; la cuenta nueva queda con
    # el valor por defecto de la columna.
    valid = _valid_lang(lang)
    if valid:
        set_oauth_lang_cookie(response, valid, _STATE_TTL_MINUTES * 60, cross_site_post=cross_site_post)


async def _find_or_create_user(
    db: AsyncSession,
    email: str,
    provider: str,
    provider_user_id: str,
    language: str | None = None,
) -> User:
    # 43.2: el email se guarda y se busca en minúsculas, como en el registro.
    email = normalize_email(email)
    # 1. Existing OAuthAccount link → return that user
    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
    )
    existing_link = result.scalar_one_or_none()
    if existing_link is not None:
        user_result = await db.execute(select(User).where(User.id == existing_link.user_id))
        return user_result.scalar_one()

    # 2. Existing user with this email → link accounts, pero solo si esa
    # cuenta ya tiene el email verificado (ver _UnverifiedEmailConflict).
    user = await user_by_email(db, email)
    created = user is None

    if user is not None and not user.email_verified:
        raise _UnverifiedEmailConflict(email)

    if user is None:
        # 3. New user — derive a unique username from the email prefix
        base = re.sub(r"[^a-z0-9_.-]", "_", email.split("@")[0].lower())[:40]
        username = base
        suffix = 1
        while True:
            if not await username_taken(db, username):
                break
            username = f"{base[:36]}_{suffix}"
            suffix += 1

        user = User(
            email=email,
            username=username,
            hashed_password=None,
            display_name=base[:100],
            email_verified=True,  # provider has already verified it
        )
        # 45.1: solo al crear la cuenta. Una que ya existe guarda el suyo (E1).
        if language:
            user.language = language
        db.add(user)
        await db.flush()

    db.add(
        OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
        )
    )
    await db.commit()
    await db.refresh(user)
    if created:
        # 45.2 (ADR-66 E2): la cuenta llega verificada, así que la bienvenida sale ya.
        from app.services import email as email_svc

        email_svc.send_welcome(to=user.email, name=user.display_name, lang=user.language)
    return user
