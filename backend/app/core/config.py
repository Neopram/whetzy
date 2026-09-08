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
    TRUST_PROXY_HEADERS: bool = False

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
    AUTH_RATE_LIMIT: int = 12
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
            "https://*.pages.dev",
        ]
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _assemble_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # --- AI Tutor (Groq) -----------------------------------------------------
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "qwen/qwen3.8-27b"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # --- RAG (ChromaDB) -------------------------------------------------------
    # Empty → auto-resolved to backend/chroma_db/ relative to rag.py location.
    CHROMA_PERSIST_PATH: str = ""

    # --- Email (transaccional) -----------------------------------------------
    EMAIL_PROVIDER: str = "smtp"  # smtp | resend | log (fallback/dev)
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

    # --- Stripe (7.2) -------------------------------------------------------
    STRIPE_SECRET_KEY: str = ""         # sk_test_... or sk_live_...
    STRIPE_WEBHOOK_SECRET: str = ""     # whsec_...
    STRIPE_PRICE_PLUS: str = ""         # price_... for the Plus plan
    STRIPE_PRICE_PRO: str = ""          # price_... for the Pro plan
    STRIPE_SUCCESS_URL: str = "https://whetzy.com/billing/success"
    STRIPE_CANCEL_URL: str = "https://whetzy.com/billing/cancel"

    # --- Gamification tuning -------------------------------------------------
    MASTERY_THRESHOLD: float = 0.95
    DEFAULT_MODULE_UNLOCK_MASTERY: float = 0.7


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
