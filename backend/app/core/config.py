"""Application settings loaded from environment variables / .env file.

All values ship with sensible local-development defaults so the app can be
run out of the box with `uvicorn app.main:app --reload`, while still being
fully configurable in staging/production via environment variables.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- General ---------------------------------------------------------
    APP_NAME: str = "Whetzy"
    ENVIRONMENT: str = "development"  # development | staging | production
    # False by default — set DEBUG=true in .env for local development only.
    # Keeps /docs and /redoc hidden in production (ASVS V14.4).
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    # When True, trust the leftmost IP in X-Forwarded-For for rate limiting.
    # Only enable behind a known reverse proxy (ASVS V11.2).
    # Detras de un proxy (Railway, Cloudflare) esto tiene que estar en true o
    # `request.client.host` es la IP del proxy — la misma para todo el mundo — y
    # el limite por IP pasa a ser un limite global compartido por todos los
    # usuarios. Medido en produccion el 2026-09-20: 14 de 20 intentos de login
    # desde un solo cliente devolvian 429. La cabecera se lee por la derecha
    # (ver `_client_key`), que es la parte que anade el proxy y no el cliente.
    TRUST_PROXY_HEADERS: bool = True
    # Saltos de proxy de confianza entre el cliente y la app. Railway pone uno.
    TRUSTED_PROXY_HOPS: int = 1

    # --- Database (PostgreSQL, async via asyncpg) -------------------------
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/learning_engine"
    )
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # --- Redis (caching, rate limiting, bandit state, etc.) ---------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Auth / JWT --------------------------------------------------------
    SECRET_KEY: str = "insecure-dev-secret-key-change-me-in-production-0123456789"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # --- Rate limiting -------------------------------------------------------
    # /auth and /tutor get a stricter budget than the rest of the API (see
    # RateLimitMiddleware). 12/min is right for production traffic but too
    # tight for an E2E suite that registers a fresh user per test — override
    # via env var for local/CI E2E runs, never in production.
    # Presupuesto por minuto y por IP para las rutas donde se adivinan
    # credenciales (login, registro, reset). No es la defensa principal contra
    # el relleno de credenciales —eso es el bloqueo progresivo por cuenta de
    # `auth_hardening`—, asi que puede ser holgado sin perder seguridad. Valia
    # 12 y lo compartian **todas** las rutas de auth, incluida `/auth/me`, que
    # la app llama en cada arranque: treinta personas registrandose a la vez
    # (un aula, un hilo que funciona) se comian 429 casi todas.
    AUTH_RATE_LIMIT: int = 60
    DEFAULT_RATE_LIMIT: int = 120

    # --- CORS ---------------------------------------------------------------
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "https://whetzy.com",
            "https://www.whetzy.com",
            "https://whetzy.pages.dev",
        ]
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _assemble_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def active_cors_origins(self) -> list[str]:
        """Origins actually handed to CORSMiddleware (22.2).

        The default list carries the localhost ports a developer needs. In
        production those must not survive: with ``allow_credentials=True`` a
        page served from ``http://localhost:5173`` on anyone's machine would
        otherwise be an approved origin against the live API. Loopback origins
        are dropped whenever ENVIRONMENT is production.
        """
        if self.ENVIRONMENT != "production":
            return self.BACKEND_CORS_ORIGINS
        return [
            origin
            for origin in self.BACKEND_CORS_ORIGINS
            if not origin.startswith(("http://localhost", "http://127.0.0.1",
                                      "https://localhost", "https://127.0.0.1"))
        ]

    # --- AI Tutor (Groq) -----------------------------------------------------
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "qwen/qwen3.8-27b"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # --- Email (transaccional) -----------------------------------------------
    # auto = se usa lo que haya (RESEND_API_KEY, si no SMTP_USER+SMTP_PASSWORD,
    # si no log). Valia "smtp" por defecto, y como el valor por defecto era
    # indistinguible de una eleccion del operador, poner solo RESEND_API_KEY no
    # activaba nada: los correos se escribian en el log y se perdian (H.30).
    EMAIL_PROVIDER: str = "auto"  # auto | smtp | resend | log
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    RESEND_API_KEY: str = ""
    EMAIL_FROM_ADDRESS: str = "noreply@whetzy.com"
    EMAIL_FROM_NAME: str = "Whetzy"
    FRONTEND_BASE_URL: str = "https://whetzy.com"

    # --- OpenTelemetry -------------------------------------------------------
    OTEL_SERVICE_NAME: str = "whetzy-backend"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""  # empty = console exporter (dev)

    # --- Observability -------------------------------------------------------
    METRICS_ENABLED: bool = True
    SENTRY_DSN: str = ""  # empty = disabled
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # --- Content admin -------------------------------------------------------
    # Set a non-empty value to enable PATCH /questions/{id} (content versioning).
    # Requests must supply X-Admin-Key: <this value>. Empty = endpoint disabled.
    CONTENT_ADMIN_KEY: str = ""

    # --- Cuenta de dueno (rol `owner`) ----------------------------------------
    # `scripts/start.sh` corre `app.services.bootstrap_owner` en cada arranque:
    # con los dos valores puestos, crea o actualiza esa cuenta (rol owner,
    # email verificado, esa contrasena). Vacios = no hace nada. La contrasena
    # vive solo en las variables de Railway, nunca en el repo.
    OWNER_EMAIL: str = ""
    OWNER_PASSWORD: str = ""

    # --- Web Push / VAPID (3.3) ----------------------------------------------
    # Generate with: python -m py_vapid --gen
    # Set VAPID_EMAIL to your contact address (required by browser push services).
    VAPID_PRIVATE_KEY: str = ""   # base64url-encoded DER EC private key
    VAPID_PUBLIC_KEY: str = ""    # base64url-encoded uncompressed public key point
    VAPID_EMAIL: str = "mailto:hello@whetzy.com"

    # --- Streak reminder (P.13) -----------------------------------------------
    # Max push reminders per user per day (enforced client-side; limit at backend too).
    STREAK_REMINDER_MAX_PER_DAY: int = 1

    # --- OAuth social login (19.1) ------------------------------------------
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    # Base URL used to build OAuth callback URIs (should be the backend origin).
    OAUTH_REDIRECT_BASE_URL: str = "https://api-production-9751.up.railway.app"

    # --- Stripe (7.2) -------------------------------------------------------
    STRIPE_SECRET_KEY: str = ""         # sk_test_... or sk_live_...
    STRIPE_WEBHOOK_SECRET: str = ""     # whsec_...
    STRIPE_PRICE_PLUS: str = ""         # price_... for the Plus plan
    STRIPE_PRICE_PRO: str = ""          # price_... for the Pro plan
    STRIPE_PRICE_CREATOR: str = ""      # price_... for the Creator plan (ADR-45)
    # Monthly list price per subscription tier, in USD (ADR-21).
    # The admin revenue panel multiplies these by the number of *active*
    # subscriptions found in the DB; they are settings, not magic numbers,
    # so a price change never means editing an endpoint.
    # Confirmed by the owner 2026-09-24 (ADR-45): code tier ``plus`` is sold as
    # "Pro" ($14.99), ``pro`` as "Pro Max" ($19.99), ``creator`` as "Creador"
    # ($99.99, publishes bootcamps; 80/20 on each sale).
    PLAN_PRICE_PLUS_USD: float = 14.99
    PLAN_PRICE_PRO_USD: float = 19.99
    PLAN_PRICE_CREATOR_USD: float = 99.99
    # Publicar cursos exige el plan Creador. Apagado hasta que el cobro esté
    # abierto (H.19/H.29): exigir un plan que nadie puede comprar cerraría el
    # marketplace. Se enciende en Railway con CREATOR_PLAN_REQUIRED=true.
    CREATOR_PLAN_REQUIRED: bool = False

    STRIPE_SUCCESS_URL: str = "https://whetzy.com/billing/success"
    STRIPE_CANCEL_URL: str = "https://whetzy.com/billing/cancel"

    # --- Paddle (H.29 - Merchant of Record) ----------------------------------
    PADDLE_API_KEY: str = ""                # pad_live_... or pad_sand_...
    PADDLE_WEBHOOK_SECRET: str = ""         # Paddle webhook signing secret
    PADDLE_VENDOR_ID: str = ""              # Vendor ID from Paddle dashboard
    PADDLE_TAX_ID: str = ""                 # Tax ID for Grecia (DAC7)
    # Instructor payout webhook for Paddle events
    PADDLE_PAYOUT_WEBHOOK_URL: str = "https://api-production-9751.up.railway.app/api/v1/webhooks/paddle"

    # --- A/B experiments -----------------------------------------------------
    # Fraction of users assigned to the DKT skill-selection cohort (0.0–1.0).
    # Assignment is deterministic: hash(user_id) % 1000 < DKT_AB_RATIO * 1000.
    DKT_AB_RATIO: float = 0.5

    # --- Gamification tuning -------------------------------------------------
    MASTERY_THRESHOLD: float = 0.95
    DEFAULT_MODULE_UNLOCK_MASTERY: float = 0.7


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()




