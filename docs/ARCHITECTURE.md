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
        ├── ChromaDB (local fs)        RAG vector index (persistence on disk)
        └── Groq API                   LLM for AI tutor (qwen3.8-27b)
```

## Backend layer map

```
app/
├── api/v1/endpoints/     # HTTP layer — thin, delegates to services
│   ├── auth.py           # register, login, refresh, me, password reset, email verify
│   ├── quiz.py           # start, answer, skip, end quiz sessions
│   ├── progress.py       # dashboard, skills, curriculum, DKT predictions
│   ├── placement.py      # adaptive placement test
│   ├── glossary.py       # bilingual glossary by track
│   ├── duels.py          # async 1v1 duels
│   ├── tutor.py          # Groq AI explanations + RAG context
│   └── social.py         # league/leaderboard
│
├── services/             # Business logic
│   ├── engine/           # Adaptive algorithms (pure Python, no I/O)
│   │   ├── bkt.py        # Bayesian Knowledge Tracing
│   │   ├── elo.py        # Elo rating for difficulty matching
│   │   ├── fsrs.py       # FSRS spaced repetition scheduler
│   │   └── bandit.py     # Thompson Sampling multi-armed bandit
│   ├── gamification/     # XP, streaks, leagues, badges, missions
│   ├── ai/               # Groq client + RAG (ChromaDB)
│   ├── quiz.py           # Quiz session orchestration (combines engine/)
│   ├── email.py          # Transactional email (SMTP / Resend / log fallback)
│   └── dkt.py            # Deep Knowledge Tracing (PyTorch LSTM, optional)
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

## Middleware stack (LIFO applied, so listed outer→inner)

1. `CORSMiddleware` — configured origins
2. `RequestIDMiddleware` — UUID per request, X-Request-ID header, JSON access log
3. `RateLimitMiddleware` — 12/min for /auth + /tutor; 120/min default
4. `SecurityHeadersMiddleware` — HSTS, CSP, X-Frame-Options, etc.

## Invariants (never break)

- Railway deploy is **manual** — no GitHub webhook. Push code, then deploy via Railway UI.
- Alembic migrations via `alembic revision --autogenerate`, **never** `Base.metadata.create_all` in production.
- JWT secret lives in `SECRET_KEY` env var. Access tokens expire in 30 min; refresh tokens in 30 days.
- Raw password reset / email verification tokens never stored — only SHA-256 hash.
- DKT (PyTorch) is optional — falls back to exponential moving average if torch is unavailable.
