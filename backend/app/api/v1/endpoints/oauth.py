"""OAuth 2.0 social login — GitHub and Google (redirect flow, no third-party JS SDK).

Flow:
  1. Browser → GET /auth/oauth/{provider}/start
     Backend stores a CSRF state nonce and redirects to the provider auth page.
  2. Provider → GET /auth/oauth/{provider}/callback?code=…&state=…
     Backend validates state, exchanges code for provider token, resolves email,
     finds or creates user, issues JWT pair and redirects to FRONTEND_BASE_URL
     with both tokens in HttpOnly cookies (`set_auth_cookies`), never in the URL.
  3. Frontend loads with the session cookie already set, like after a password login.
"""
from __future__ import annotations

import re
import secrets
import urllib.parse
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.security import create_access_token, create_refresh_token
from app.models.oauth import OAuthAccount, OAuthState
from app.models.user import User
from app.services import account_deletion

router = APIRouter()

_STATE_TTL_MINUTES = 10

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
}

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
    Google» que responde 503 al pulsarlo es peor que ningún botón.
    """
    response.headers["Cache-Control"] = "public, max-age=3600"
    return {"providers": [name for name, cfg in _PROVIDERS.items() if cfg["client_id"]()]}


# --------------------------------------------------------------------------
# /start
# --------------------------------------------------------------------------

@router.get("/{provider}/start")
async def oauth_start(
    provider: str,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    cfg = _get_provider(provider)

    if provider != "test" and not cfg["client_id"]():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{provider} login is not configured on this server",
        )

    state = secrets.token_urlsafe(32)
    db.add(
        OAuthState(
            state=state,
            provider=provider,
            expires_at=datetime.now(UTC) + timedelta(minutes=_STATE_TTL_MINUTES),
        )
    )
    await db.commit()

    if provider == "test":
        # Test provider: skip real redirect, go straight to our own callback
        callback = _callback_uri("test")
        return RedirectResponse(
            url=f"{callback}?code=test-code&state={state}",
            status_code=302,
        )

    params: dict[str, str] = {
        "client_id": cfg["client_id"](),
        "redirect_uri": _callback_uri(provider),
        "scope": cfg["scope"],
        "state": state,
    }
    if provider == "google":
        params["response_type"] = "code"
        params["access_type"] = "offline"

    auth_url = cfg["auth_url"] + "?" + urllib.parse.urlencode(params)
    return RedirectResponse(url=auth_url, status_code=302)


# --------------------------------------------------------------------------
# /callback
# --------------------------------------------------------------------------

@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    _get_provider(provider)  # validates name

    # Validate and consume state nonce (CSRF protection)
    result = await db.execute(select(OAuthState).where(OAuthState.state == state))
    oauth_state = result.scalar_one_or_none()

    if oauth_state is None or oauth_state.provider != provider:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    if oauth_state.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        await db.delete(oauth_state)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth state expired")

    await db.delete(oauth_state)
    await db.commit()

    # Resolve email and provider user ID
    if provider == "test":
        email: str | None = f"oauth-{code}@example.com"
        provider_user_id = f"test-{code}"
    else:
        async with httpx.AsyncClient(timeout=10) as client:
            token_data = await _exchange_code(client, provider, code)
            provider_token = token_data.get("access_token")
            if not provider_token:
                return RedirectResponse(
                    url=f"{settings.FRONTEND_BASE_URL}/?oauth_error=provider_error",
                    status_code=302,
                )
            email, provider_user_id = await _get_user_info(client, provider, provider_token)

    if not email:
        return RedirectResponse(
            url=f"{settings.FRONTEND_BASE_URL}/?oauth_error=email_required",
            status_code=302,
        )

    user = await _find_or_create_user(db, email, provider, provider_user_id)
    if not user.is_active and not await account_deletion.restore_if_pending(db, user):
        return RedirectResponse(
            url=f"{settings.FRONTEND_BASE_URL}/?oauth_error=account_inactive",
            status_code=302,
        )

    from app.core.cookies import set_auth_cookies

    access_token = create_access_token(user.id, jwt_version=user.jwt_version)
    refresh_token = create_refresh_token(user.id, jwt_version=user.jwt_version)

    redirect = RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/", status_code=302)
    set_auth_cookies(redirect, access_token, refresh_token)
    return redirect


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

async def _exchange_code(
    client: httpx.AsyncClient,
    provider: str,
    code: str,
) -> dict[str, Any]:
    cfg = _PROVIDERS[provider]
    data: dict[str, str] = {
        "client_id": cfg["client_id"](),
        "client_secret": cfg["client_secret"](),
        "code": code,
        "redirect_uri": _callback_uri(provider),
    }
    if provider == "google":
        data["grant_type"] = "authorization_code"
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


async def _find_or_create_user(
    db: AsyncSession,
    email: str,
    provider: str,
    provider_user_id: str,
) -> User:
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

    # 2. Existing user with this email → link accounts
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()

    if user is None:
        # 3. New user — derive a unique username from the email prefix
        base = re.sub(r"[^a-z0-9_.-]", "_", email.split("@")[0].lower())[:40]
        username = base
        suffix = 1
        while True:
            taken = await db.execute(select(User).where(User.username == username))
            if taken.scalar_one_or_none() is None:
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
    return user
