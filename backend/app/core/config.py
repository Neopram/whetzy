"""Application settings loaded from environment variables / .env file.

All values ship with sensible local-development defaults so the app can be
run out of the box with `uvicorn app.main:app --reload`, while still being
fully configurable in staging/production via environment variables.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# La clave de desarrollo y el marcador de `.env.example`. Ninguna de las dos
# puede firmar tokens en producción (S.16).
_DEV_SECRET_KEY = "insecure-dev-secret-key-change-me-in-production-0123456789"
_PLACEHOLDER_SECRET_KEYS = frozenset(
    {_DEV_SECRET_KEY, "change-me-to-a-64-char-random-hex-string"}
)
SECRET_KEY_MIN_LENGTH = 32


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
    SECRET_KEY: str = _DEV_SECRET_KEY
    JWT_ALGORITHM: str = "HS256"
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    COOKIE_DOMAIN: str = ""
    COOKIE_SECURE: bool = True

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
            # La app de Capacitor (frontend/capacitor.config.ts, `server.hostname`):
            # Android la sirve por https y iOS por su esquema propio.
            "https://app.whetzy.com",
            "capacitor://app.whetzy.com",
        ]
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _assemble_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator(
        "PADDLE_API_KEY",
        "PADDLE_WEBHOOK_SECRET",
        "PADDLE_ENVIRONMENT",
        "PADDLE_CLIENT_TOKEN",
        "PADDLE_PRICE_PLUS",
        "PADDLE_PRICE_PRO",
        "PADDLE_PRICE_CERTIFICATION",
        "PADDLE_PRICE_PLUS_ANNUAL",
        "PADDLE_PRICE_PRO_ANNUAL",
        mode="before",
    )
    @classmethod
    def _strip_paddle_values(cls, v: Any) -> Any:
        # Un espacio o salto de línea pegado con el valor en Railway rompe la
        # firma del webhook (401 «Invalid Paddle-Signature») sin decir por qué.
        return v.strip() if isinstance(v, str) else v

    @model_validator(mode="after")
    def _production_needs_a_real_secret_key(self) -> Settings:
        """En producción, el arranque falla con una SECRET_KEY de ejemplo o corta (S.16).

        `verify_token` acepta HS256 con `SECRET_KEY` aunque haya clave RS256
        (`_verification_keys`, para los tokens de antes de la migración): una
        clave conocida en producción deja a cualquiera firmar la sesión de
        cualquier alumno. Como esto corre al construir `Settings`, revienta
        antes de `alembic`, del cargador y de gunicorn (`start.sh` va con
        `set -e`): el contenedor nuevo no llega a responder a `/health`.
        """
        if self.ENVIRONMENT != "production":
            return self
        key = self.SECRET_KEY.strip()
        if key in _PLACEHOLDER_SECRET_KEYS:
            raise ValueError(
                "SECRET_KEY es la de ejemplo: en producción hace falta una clave "
                "aleatoria propia (python -c 'import secrets; print(secrets.token_hex(32))')"
            )
        if len(key) < SECRET_KEY_MIN_LENGTH:
            raise ValueError(
                f"SECRET_KEY tiene {len(key)} caracteres: en producción hacen falta "
                f"al menos {SECRET_KEY_MIN_LENGTH}"
            )
        return self

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
    # 39.11: techo global de llamadas al LLM por día UTC y por proceso (sin Redis en
    # Railway: con 2 workers el techo real es el doble). Al superarlo se responde con
    # el contexto de la pregunta (NullProvider), no con un error. 0 = sin techo.
    LLM_DAILY_CALL_LIMIT: int = 2000
    # 39.12 (ADR-50f): proveedor de respaldo compatible con OpenAI. Vacío = sin respaldo.
    LLM_FALLBACK_BASE_URL: str = ""
    LLM_FALLBACK_API_KEY: str = ""
    LLM_FALLBACK_MODEL: str = ""

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
    # 45.4: buzón de prueba. Con el proveedor `log`, cada correo se guarda como JSON
    # en esta carpeta para que el e2e lea el enlace. Vacío = apagado; en producción
    # no escribe nunca (`email._send_log`).
    EMAIL_OUTBOX_DIR: str = ""
    FRONTEND_BASE_URL: str = "https://whetzy.com"
    # Base pública de esta API: el enlace de baja de un correo (RFC 8058) tiene
    # que aceptar un POST, así que apunta aquí y no al frontend.
    API_PUBLIC_BASE_URL: str = "https://api-production-9751.up.railway.app"

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
    # Tope de endpoints distintos por usuario en POST /push/subscribe (S.15):
    # sin él, una cuenta podía acumular endpoints sin límite.
    PUSH_MAX_SUBSCRIPTIONS_PER_USER: int = 10

    # --- Streak reminder (P.13) -----------------------------------------------
    # Max push reminders per user per day (enforced client-side; limit at backend too).
    STREAK_REMINDER_MAX_PER_DAY: int = 1

    # --- OAuth social login (19.1) ------------------------------------------
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    # Sign in with Apple (19.2): Services ID, Team ID, Key ID y la clave .p8 (PEM;
    # en una línea con «\n»). Las cuatro o ninguna. No existen hasta H.2.
    APPLE_CLIENT_ID: str = ""
    APPLE_TEAM_ID: str = ""
    APPLE_KEY_ID: str = ""
    APPLE_PRIVATE_KEY: str = ""
    # Base URL used to build OAuth callback URIs (should be the backend origin).
    OAUTH_REDIRECT_BASE_URL: str = "https://api-production-9751.up.railway.app"

    # --- Stripe (7.2) -------------------------------------------------------
    STRIPE_SECRET_KEY: str = ""         # sk_test_... or sk_live_...
    STRIPE_WEBHOOK_SECRET: str = ""     # whsec_...
    STRIPE_PRICE_PLUS: str = ""         # price_... for the Plus plan
    STRIPE_PRICE_PRO: str = ""          # price_... for the Pro plan
    STRIPE_PRICE_CREATOR: str = ""      # price_... for the Creator plan (ADR-41)
    # Monthly list price per subscription tier, in USD (ADR-21).
    # The admin revenue panel multiplies these by the number of *active*
    # subscriptions found in the DB; they are settings, not magic numbers,
    # so a price change never means editing an endpoint.
    # Confirmed by the owner 2026-09-24 (ADR-41): code tier ``plus`` is sold as
    # "Pro" ($14.99), ``pro`` as "Pro Max" ($19.99), ``creator`` as "Creador"
    # ($99.99, publishes bootcamps; 80/20 on each sale).
    PLAN_PRICE_PLUS_USD: float = 14.99
    PLAN_PRICE_PRO_USD: float = 19.99
    PLAN_PRICE_CREATOR_USD: float = 99.99
    # Publicar cursos exige el plan Creador. Apagado hasta que el cobro esté
    # abierto (H.19/H.29): exigir un plan que nadie puede comprar cerraría el
    # marketplace. Se enciende en Railway con CREATOR_PLAN_REQUIRED=true.
    CREATOR_PLAN_REQUIRED: bool = False
    # Programa de referidos (ADR-35, ECONOMIA §3): pausa manual. Además se pausa
    # solo si el fraude supera el 5 % dos semanas seguidas (§3.5). Pausado, el
    # job ni activa ni abona; los referidos esperan, no se pierden.
    REFERRALS_PAUSED: bool = False
    # Pro Max (`pro`) trae el tutor ilimitado; Pro (`plus`) tiene este cupo de
    # explicaciones por día UTC (ADR-49; el dueño confirmó 20 el 2026-09-25).
    # El frontend lo muestra desde `src/lib/plans.ts`, y un test exige que coincidan.
    TUTOR_DAILY_LIMIT_PLUS: int = 20
    # S.5: `conversation_history` lo manda el cliente y se pega sin filtrar
    # a los mensajes que ve el LLM (`provider.py`) -- sin tope, una petición
    # podía llevar cientos de turnos o turnos enormes y disparar el coste
    # real por llamada muy por encima de lo que el cupo por petición asume
    # (crítico en Pro Max, que no tiene cupo de peticiones, ADR-49).
    TUTOR_HISTORY_MAX_TURNS: int = 20
    TUTOR_HISTORY_MAX_CHARS_PER_TURN: int = 2000
    # 41.17: cinturón de seguridad por tokens, no una cifra de negocio (nunca
    # bloquea a quien ADR-49 ya declaró ilimitado -- ver tutor_quota.
    # daily_token_limit). Con TUTOR_HISTORY_MAX_TURNS × _MAX_CHARS_PER_TURN
    # el peor caso de una sola llamada son ~12.000 tokens
    # (tutor_quota.TOKEN_RESERVE_ESTIMATE); 20 llamadas al tope de Plus darían
    # un techo teórico de 240.000. Este número va por debajo, para que de
    # verdad frene varias conversaciones enormes seguidas en vez de limitarse
    # a repetir lo que ya hace TUTOR_DAILY_LIMIT_PLUS.
    TUTOR_DAILY_TOKEN_LIMIT_PLUS: int = 150_000
    # Examen certificador: pago único por track de certificación (ADR-49).
    # El flag se queda apagado hasta que abra el cobro (H.19/H.29), por la misma
    # razón que CREATOR_PLAN_REQUIRED: exigir un pago imposible cierra el producto.
    CERTIFICATION_PAYWALL: bool = False
    CERTIFICATION_PRICE_USD: float = 39.99
    # Plan Free (ADR-50a, 39.4): preguntas nuevas y lecciones por día UTC. Apagado
    # hasta que abra el cobro (H.19/H.29), igual que los dos flags de arriba. El
    # frontend muestra las cifras desde `src/lib/plans.ts` y un test exige que coincidan.
    FREE_DAILY_QUOTA_ENABLED: bool = False
    FREE_DAILY_NEW_QUESTIONS: int = 30
    FREE_DAILY_LESSONS: int = 5

    # Banco de simulacro reservado (37.18, ADR-53 §4): el mecanismo (columna
    # `pool`, filtros en quiz.py/mock_exam.py) ya existe. El banco va por 146
    # preguntas `pool="simulacro"` (2026-10-13, 37.24) y la meta es 2 × la
    # longitud del examen por certificación (ADR-54): encenderlo antes dejaría
    # simulacros cortos o `MockExamError` ("not enough questions") — apagado
    # hasta que cada certificación llegue, igual que los flags de arriba
    # esperan a su propia dependencia.
    MOCK_EXAM_RESERVED_POOL_ENABLED: bool = False

    # --- Open Badges 3.0 / Verifiable Credentials (29.10, ADR-37) -----------
    # Ed25519 private key in PEM format. Generate with:
    #   python -c "from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey; from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption; k=Ed25519PrivateKey.generate(); print(k.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode())"
    # Keep in env, never in the repo.
    OB_SIGNING_PRIVATE_KEY: str = ""
    OB_SIGNING_PUBLIC_KEY: str = ""  # auto-derived from private if empty

    STRIPE_SUCCESS_URL: str = "https://whetzy.com/billing/success"
    STRIPE_CANCEL_URL: str = "https://whetzy.com/billing/cancel"

    # --- RevenueCat / in-app purchases (17.14) ------------------------------
    # Mobile IAP (StoreKit / Google Play Billing) is the only checkout that
    # works without a company (ADR-47, legal/h21-decision.md) — RevenueCat is
    # the client SDK + webhook layer over both stores. Empty by default (no
    # live keys): the mobile client shows no purchase UI and this webhook
    # rejects every request until REVENUECAT_WEBHOOK_AUTHORIZATION is set.
    #
    # Auth: RevenueCat signs each webhook with the Authorization header value
    # configured in its dashboard (not HMAC by default — verified live against
    # revenuecat.com/docs/integrations/webhooks, 2026-09-27); the handler does
    # a constant-time compare against this same value.
    REVENUECAT_WEBHOOK_AUTHORIZATION: str = ""
    # RevenueCat "entitlement identifier" (configured in its dashboard, not a
    # store product id) → Whetzy tier, same shape as STRIPE_PRICE_* → tier.
    REVENUECAT_ENTITLEMENT_PLUS: str = ""   # "Pro" ($14.99/mes, ADR-41)
    REVENUECAT_ENTITLEMENT_PRO: str = ""    # "Pro Max" ($19.99/mes, ADR-41)

    # --- Paddle (H.29 - Merchant of Record) ----------------------------------
    PADDLE_API_KEY: str = ""                # pdl_live_apikey_... (live) o la de sandbox
    PADDLE_WEBHOOK_SECRET: str = ""         # pdl_ntfset_... (Developer tools > Notifications)
    PADDLE_VENDOR_ID: str = ""              # Vendor ID from Paddle dashboard
    PADDLE_TAX_ID: str = ""                 # Tax ID for Grecia (DAC7)
    # Paddle Billing, pago web (H.29; el dueño descartó Stripe el 2026-10-01).
    # "sandbox" usa sandbox-api.paddle.com y dinero simulado; "production", el real.
    PADDLE_ENVIRONMENT: str = "sandbox"
    # Token de cliente de Paddle.js: es público (va en la web), no es un secreto.
    PADDLE_CLIENT_TOKEN: str = ""
    # Ids de precio (`pri_...`) → plan. Pro 14,99 $/mes = "plus", Pro Max
    # 19,99 $/mes = "pro" (ADR-41), certificación 39,99 $ pago único (ADR-49).
    PADDLE_PRICE_PLUS: str = ""
    PADDLE_PRICE_PRO: str = ""
    PADDLE_PRICE_CERTIFICATION: str = ""
    # Plan anual (40.9): el precio y el reembolso son del dueño (ADR-41) — aquí
    # solo la variable que lo enciende y los ids de precio, vacíos hasta que
    # los dé Paddle. Apagado por defecto, igual que los flags de arriba.
    ANNUAL_PLAN_ENABLED: bool = False
    PADDLE_PRICE_PLUS_ANNUAL: str = ""
    PADDLE_PRICE_PRO_ANNUAL: str = ""
    # Antigüedad máxima aceptada de un webhook (Paddle recomienda 5 s).
    PADDLE_WEBHOOK_TOLERANCE_SECONDS: int = 5
    # Instructor payout webhook for Paddle events
    PADDLE_PAYOUT_WEBHOOK_URL: str = "https://api-production-9751.up.railway.app/api/v1/webhooks/paddle"
    # Gate for the instructor marketplace enroll endpoint (B1).
    # Off by default until Paddle is live; set True in staging/prod once the
    # payment webhook drives enrollment instead of direct API calls.
    INSTRUCTOR_MARKETPLACE_ENABLED: bool = False
    # Perfil público por username (0.3). Apagado hasta que exista el opt-in y lo
    # recojan la política de privacidad: hoy publicaría dominio, racha y
    # certificados de cualquier alumno sin login ni consentimiento.
    PUBLIC_PROFILES_ENABLED: bool = False
    # Gate for the public course catalog (28.8), independent of
    # INSTRUCTOR_MARKETPLACE_ENABLED: a course can be browsable before
    # enrollment/payment is live. Off by default — nothing is published yet.
    MARKETPLACE_PUBLIC: bool = False

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




