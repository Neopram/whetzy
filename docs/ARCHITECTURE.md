# Whetzy — Architecture

## System overview

```
Frontend (React + Capacitor)          whetzy.com / whetzy.pages.dev
        │
        │ HTTPS / REST
        ▼
Backend (FastAPI)              api-production-9751.up.railway.app
        │
        ├── PostgreSQL (Railway)       primary data store
        ├── BM25 index (in-memory)     RAG retrieval, built at startup from the DB
        ├── Groq API                   LLM for AI tutor (qwen3.8-27b)
        ├── Paddle                     web payments (Paddle.js en /checkout + webhook firmado; H.29)
        ├── Resend                     correo de la cuenta
        └── Sentry                     errores del servidor (región UE)
```

> **RAG note.** ChromaDB + sentence-transformers were removed (they OOM'd on the
> Railway free tier, so the index never built in production and the tutor was not
> actually grounded). Retrieval is now `rank-bm25`, pure Python, in-memory, built
> from the DB during lifespan: 1323 docs in 0.57 s, +16 MB RSS, self-retrieval
> top-3 at 99.6 % ES / 99.7 % EN.

## Backend layer map

```
app/
├── api/v1/endpoints/     # HTTP layer — thin, delegates to services. 67 routes (+4 root: /, /health, /health/live, /health/ready) = 71 total.
│   ├── auth.py           # register, login, refresh, me, password reset, email verify, delete
│   ├── quiz.py           # start, answer, end, review-due
│   ├── progress.py       # dashboard, skills, curriculum, DKT predictions, churn risk
│   ├── placement.py      # adaptive placement test
│   ├── glossary.py       # bilingual glossary by track
│   ├── duels.py          # async 1v1 duels (challenge, join, answer, result)
│   ├── exams.py          # timed certification mock exam + per-domain report
│   ├── tutor.py          # Groq explanations + BM25 RAG context
│   ├── content.py        # tracks, author agent, QA agent, duplicates, versioned edits
│   ├── billing.py        # Paddle (config, cancel), RevenueCat webhook, subscription state; Stripe sin uso (H.29)
│   ├── push.py           # web push: VAPID key, subscribe, preferences, streak reminders
│   ├── analytics.py      # admin funnel + dashboard (X-Admin-Key)
│   ├── ml.py             # model version, rollback, A/B cohort stats
│   ├── reports.py        # user-reported broken questions
│   ├── export.py         # GDPR data export
│   └── social.py         # league / leaderboard, badges, missions
│
├── services/             # Business logic
│   ├── engine/           # Adaptive algorithms (pure Python, no I/O)
│   │   ├── bkt.py        # Bayesian Knowledge Tracing
│   │   ├── elo.py        # Elo rating for difficulty matching
│   │   ├── fsrs.py       # FSRS spaced repetition scheduler
│   │   ├── bandit.py     # Thompson Sampling multi-armed bandit
│   │   ├── placement.py  # placement ability estimation
│   │   └── scheduler.py  # review scheduling on top of FSRS
│   ├── gamification/     # XP, streaks, leagues, badges, missions
│   ├── ai/               # provider.py (swappable LLM) · rag.py (BM25) · tutor.py
│   ├── content/          # content package
│   ├── quiz.py           # Quiz session orchestration (combines engine/)
│   ├── mock_exam.py      # certification mock exam scoring + domain breakdown
│   ├── content_agent.py  # LLM author agent (needs GROQ_API_KEY)
│   ├── content_qa.py     # QA agent: structural checks + optional LLM pass
│   ├── duplicate_detector.py  # embedding cosine similarity over the bank
│   ├── content_loader.py # idempotent ingest from content/*.json
│   ├── analytics.py      # event tracking + funnel/retention aggregation
│   ├── churn.py          # logistic churn scorer (AUC 0.91 on synthetic)
│   ├── ab_harness.py     # deterministic cohort split, BKT vs DKT
│   ├── stripe_service.py # checkout sessions + webhook handling
│   ├── push_service.py   # pywebpush sender, 410 Gone cleanup
│   ├── email.py          # Transactional email (SMTP / Resend / log fallback)
│   └── dkt.py            # Deep Knowledge Tracing (PyTorch LSTM, optional)
│
├── ml/                   # Offline ML lifecycle
│   ├── train_dkt.py      # training pipeline, temporal split
│   ├── eval_dkt.py       # DKT vs BKT evaluation harness
│   ├── benchmark_kt.py   # public benchmark (synthetic-5, Piech 2015)
│   └── registry.py       # versioned checkpoints, startup load, rollback
│
├── models/               # SQLAlchemy ORM models
├── schemas/              # Pydantic request/response schemas
├── core/                 # Config, DB, security, logging, middleware
└── alembic/              # Migrations (always via `alembic revision`, never create_all)
```

## Adaptive engine pipeline

For each quiz question:

1. **BKT** — estimates P(known) per skill from answer history
2. **Elo** — selects questions at the right difficulty band
3. **FSRS** — schedules future reviews (spaced repetition)
4. **Thompson Bandit** — balances new content vs. review

These are pure functions in `services/engine/` — no DB I/O, fully unit-tested.

## Data model (key tables)

| Table | Purpose |
|---|---|
| `users` | Account, XP, streak, language, email_verified |
| `tracks / modules / skills / questions` | Content hierarchy |
| `user_skill_states` | Per-user BKT/Elo/FSRS state |
| `study_sessions / responses` | Quiz history |
| `duels` | Async 1v1 duel state |
| `leagues / league_entries` | Weekly competitive leagues |
| `badges / user_badges / missions / user_missions` | Gamification |
| `password_reset_tokens` | Single-use password reset (SHA-256 stored) |
| `email_verification_tokens` | Email verification (SHA-256 stored) |
| `domains` | Certification exam domains with official weights (track 8 = AWS CLF-C02) |
| `mock_exam_attempts` | Timed exam attempts, per-domain scoring |
| `analytics_events` | Funnel/retention event stream |
| `push_subscriptions` | Web push endpoints (VAPID) |
| `question_reports` | User-reported broken questions |

## Content

Live numbers come from `python scripts/check_docs.py` (they are also the `Contenido`
row of `docs/AUTONOMOUS_STATE.md`); as of 2026-10-02: **10,952 questions / 35 tracks /
723 skills / 723 lessons / 1,058 glossary terms**, every question with a canonical
`source`. Five certification tracks (AWS CLF-C02, SAA-C03, AIF-C01, PCEP, ISC2 CC)
carry official domains with verified weights (`exam_domain` + `exam_weight_pct`).
Executable questions (`fill_blank_exec` / `fix_bug` / `sql_exec` / `js_exec`) have
their expected output verified in CI by actually running the reference code in
CPython / sqlite3, and since 2026-10-01 also the opposite: an empty blank or the
unfixed buggy code must **not** print the answer, and every fill-in exercise must
have a `___` (`tests/content/test_exec_questions.py::TestNoFreeAnswers`). Eight tracks
are ≥ 15 % executable; the per-track floors live in `scripts/check_question_bank.py`.

**Grading is server-side.** The code runs in the learner's browser (Pyodide, sql.js,
a JS worker), but `POST /quiz/answer` decides correctness: executable types send the
`exec_output` the run produced and `fill_blank` sends the typed `answer_text`; the
server compares them with the stored answer in the learner's language. A request
without that evidence is graded wrong — until 2026-10-01 the client sent only
`selected_index: 1` and the server believed it. The output itself still comes from
the browser, so a forged `exec_output` is possible; running the code server-side
would close that and is not built. Sources are
free and legally reusable or cited only (ADR-11; inventory in
`docs/CATALOGO_MAESTRO.md` §2.1).

Questions are versioned: `Question.content_version` bumps on edit and
`Response.question_version` stamps the version answered, so correcting a question
never rewrites history.

## Middleware stack (LIFO applied, so listed outer→inner)

1. `CORSMiddleware` — configured origins
2. `RequestIDMiddleware` — UUID per request, X-Request-ID header, JSON access log
3. `RateLimitMiddleware` — 12/min for /auth + /tutor; 120/min default
4. `SecurityHeadersMiddleware` — HSTS, CSP, X-Frame-Options, etc.

## Invariants (never break)

- Railway deploy is **automatic** from `master` (verified 2026-09-16, ledger H.16): a commit reaching `master` — merged by the owner, ADR-45 — runs migrations + `content_loader` in production. Push only with `pytest tests/content` and `check_question_bank.py` green.
- Cloudflare Pages is **Git-connected**: a push to `master` builds and publishes to production (verified 2026-09-24); other branches get previews. Manual `npx wrangler pages deploy dist --project-name whetzy --branch main` from `frontend/` still works (RUNBOOK §1). `node scripts/check-deployed.mjs` must PASS after every deploy.
- Auth is email + password today; social login lands in Serie 19 (GitHub/Google web → Sign in with Apple → Google native), and Sign in with Apple is mandatory before any App Store submission once another OAuth exists (ADR-13).
- Alembic migrations via `alembic revision --autogenerate`, **never** `Base.metadata.create_all` in production.
- JWT secret lives in `SECRET_KEY` env var. Access tokens expire in 30 min; refresh tokens in 30 days.
- Raw password reset / email verification tokens never stored — only SHA-256 hash.
- DKT (PyTorch) is optional — falls back to exponential moving average if torch is unavailable.

## Threat model (STRIDE)

| Categoría | Amenaza concreta en Whetzy | Activo | Mitigación hoy | Dónde está en el código | Estado |
|---|---|---|---|---|---|
| **Spoofing** | Suplantación mediante JWT fraudulento | Cuenta de usuario | JWT firmado con `SECRET_KEY` + verificación en `get_current_user`; timeout 30 min + refresh en 30 días | `backend/app/core/security.py:_create_token`, `backend/app/core/security.py:get_current_user` | MITIGADO |
| **Spoofing** | Timing attack en validación de password | Contraseña | Dummy hash para comparación constante (ASVS V2.2) | `backend/app/core/security.py:31-32 (_DUMMY_HASH)` | MITIGADO |
| **Spoofing** | Credential stuffing contra /auth/login | Contraseña | Rate limit 12 req/min en /auth endpoints | `backend/app/core/security_middleware.py:54-56` | PARCIAL |
| **Spoofing** | Account takeover via password reset | Reset token | Tokens single-use con SHA-256 hash (nunca plain) | `backend/app/models/auth.py`, `backend/app/core/security.py` | MITIGADO |
| **Tampering** | MITM en tránsito HTTP → HTTPS | Datos en tránsito | HSTS `max-age=63072000; includeSubDomains; preload` en producción | `backend/app/core/security_middleware.py:49` | MITIGADO |
| **Tampering** | Clickjacking (X-Frame-Options) | UI del navegador | `X-Frame-Options: DENY` en todos los responses | `backend/app/core/security_middleware.py:25` | MITIGADO |
| **Tampering** | Content-Type sniffing (MIME type bypass) | Ejecución de scripts | `X-Content-Type-Options: nosniff` | `backend/app/core/security_middleware.py:24` | MITIGADO |
| **Tampering** | Inyección en código ejecutable (fill_blank_exec / fix_bug / sql_exec) | Verificación de ejercicios | Ejecución en CI sobre código de referencia; Pyodide/sql.js en sandbox WASM aislado del DOM | `backend/tests/content/test_exec_questions.py`, `frontend/src/hooks/useRuntime.ts` | MITIGADO |
| **Tampering** | JWT token falsificado (sin verificar firma) | JWT forjado | JWT verificado con `jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])`; `jose` verifica la firma por defecto y un `JWTError` se traduce en 401 | `backend/app/core/security.py:get_token_payload` | MITIGADO |
| **Repudiation** | Negación de transacciones / cambios | Auditoría de cambios | Event log en `analytics_events` para todas las sesiones; password reset tokens son single-use y registrados | `backend/app/models/analytics.py`, `backend/app/services/analytics.py` | MITIGADO |
| **Repudiation** | Negación de consumo de Groq API | Facturas de IA | Logs de requests a Groq en `audit_log` (estructura preparada en `backend/app/models/auth.py:AuditLog`) | `backend/app/models/auth.py:AuditLog` (la tabla existe; **no hay ajuste que lo active ni escritor que registre las llamadas a Groq** — `grep -rn AUDIT_LOG_ENABLED backend/` sale vacio) | PARCIAL |
| **Information Disclosure** | Información sensible en Referrer header | Tokens en URL | `Referrer-Policy: strict-origin-when-cross-origin` (JWT nunca en URL, siempre en Authorization) | `backend/app/core/security_middleware.py:27` | MITIGADO |
| **Information Disclosure** | Exposición de OpenAPI en producción | Documentación de API | `/docs` y `/redoc` deshabilitados fuera de DEBUG mode | `backend/app/main.py:62-63` | MITIGADO |
| **Information Disclosure** | Fuga de datos via X-Admin-Key en logs | Admin key expuesta | `X-Admin-Key` solo en header (no en URL), log access solo con AUTH_RATE_LIMIT | `backend/app/api/v1/endpoints/content.py:26-29` | MITIGADO |
| **Information Disclosure** | CSP weakening (inline scripts / data URLs) | XSS | CSP `default-src 'none'; frame-ancestors 'none'; base-uri 'none'` en API responses | `backend/app/core/security_middleware.py:31` | MITIGADO |
| **Information Disclosure** | CSP del frontend (JavaScript/assets) | Frontend XSS | `_headers` Cloudflare sin CSP nativa de nivel aplicación | `frontend/public/_headers` | SIN REVISAR |
| **Denial of Service** | Brute-force en /auth/login | Credencial válida | Rate limit 12 req/min por IP | `backend/app/core/security_middleware.py:54-56, 83` | PARCIAL |
| **Denial of Service** | Flood en /quiz/answer o /tutor | Groq API cost | Rate limit 120 req/min default; sin límite per-user en token spending | `backend/app/core/security_middleware.py:66, 83` | PARCIAL |
| **Denial of Service** | Queries caras sin límite (ranking, búsqueda) | DB load | Sin límite de timeout ni per-user query budget; búsqueda por BM25 es O(n) | `backend/app/services/ai/rag.py` | SIN MITIGAR |
| **Denial of Service** | Consumo de Groq sin cuota | LLM spend | Sin metering per-user de tokens consumidos en /tutor | `backend/app/services/ai/provider.py` | SIN MITIGAR |
| **Elevation of Privilege** | Acceso a panel /admin sin role=owner | Admin data | `require_owner` decorator en cada ruta `/admin/*` | `backend/app/api/v1/endpoints/admin.py:37-44` | MITIGADO |
| **Elevation of Privilege** | Escalada via X-Admin-Key débil | Content ingest | `CONTENT_ADMIN_KEY` es secreto env (32+ chars mínimo en secrets, no en código) | `backend/app/core/config.py`, `backend/app/api/v1/endpoints/content.py:27-29` | MITIGADO |
| **Elevation of Privilege** | Role tampering en JWT payload | Privilejos | JWT decode verifica firma; role viene de DB en `get_current_user`, no de token | `backend/app/core/security.py:get_current_user` (refresh desde DB) | MITIGADO |
| **Elevation of Privilege** | DKT (PyTorch) RCE si el modelo es malicioso | ML models | DKT es opcional (fallback a EMA); carga de checkpoints verificada contra `backend/app/ml/registry.py` hashes | `backend/app/ml/registry.py`, `backend/app/services/dkt.py` | MITIGADO |

### Riesgos residuales conocidos

- **Credential stuffing (PARCIAL)**: Rate limit 12/min/IP blunta ataques pero no los detiene por completo. Alternativa futura: CAPTCHA en X intentos o 2FA. [Cerrado: 2FA TOTP y sesiones por dispositivo en `endpoints/auth_hardening.py`, fila 22x del ledger]
- **DoS en queries caras (SIN MITIGAR)**: Ranking, búsqueda y BM25 sin timeout. Impacto: Groq API no es activo (no afecta plataforma central). Aceptado porque: (1) RAG es O(n) en ~1300 docs = <100ms típico, (2) sin datos de abuso en logs. Cierra: timeout en `/tutor` + cuota de tokens por usuario en la fila **22.16**
- **Consumo de Groq sin cuota (SIN MITIGAR)**: `/tutor` no tiene metering. Impacto: runaway spend. Aceptado: Groq rate limit + costo bajo (qwen3.8). Cierra: contador de tokens en analytics_events + alertas (fila **22.16**)
- **CSP del frontend (SIN REVISAR)**: Cloudflare `_headers` no declara CSP script nativa. Riesgo bajo (Capacitor + React no usan eval), pero necesita auditoría. Cierra: fila **22.2** (cabeceras de seguridad y CSP)

### Cómo se comprueba

```bash
# Spoofing: JWT verificación
grep -n "verify_signature.*True" backend/app/core/security.py

# Spoofing: Dummy hash para timing attack
grep -n "_DUMMY_HASH" backend/app/core/security.py

# Tampering: HSTS header
grep -n "max-age=63072000" backend/app/core/security_middleware.py

# Tampering: X-Frame-Options
grep -n "X-Frame-Options" backend/app/core/security_middleware.py

# Information Disclosure: /docs oculto en producción
grep -n "docs_url.*DEBUG" backend/app/main.py

# Information Disclosure: X-Admin-Key
grep -n "CONTENT_ADMIN_KEY" backend/app/api/v1/endpoints/content.py

# Denial of Service: Rate limits
grep -n "DEFAULT_RATE_LIMIT\|AUTH_RATE_LIMIT" backend/app/core/config.py

# Elevation of Privilege: require_owner en admin
grep -n "require_owner\|require_admin" backend/app/api/v1/endpoints/admin.py

# CSP API
grep -n "Content-Security-Policy" backend/app/core/security_middleware.py

# No cookies (verificación de que no hay cookies)
grep -rn "set_cookie" backend/app/ || echo "OK: No se encontraron cookies"
```
