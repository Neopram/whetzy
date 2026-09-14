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
        └── Stripe API                 subscriptions (web checkout + webhooks)
```

> **RAG note.** ChromaDB + sentence-transformers were removed (they OOM'd on the
> Railway free tier, so the index never built in production and the tutor was not
> actually grounded). Retrieval is now `rank-bm25`, pure Python, in-memory, built
> from the DB during lifespan: 1323 docs in 0.57 s, +16 MB RSS, self-retrieval
> top-3 at 99.6 % ES / 99.7 % EN.

## Backend layer map

```
app/
├── api/v1/endpoints/     # HTTP layer — thin, delegates to services. 61 routes.
│   ├── auth.py           # register, login, refresh, me, password reset, email verify, delete
│   ├── quiz.py           # start, answer, end, review-due
│   ├── progress.py       # dashboard, skills, curriculum, DKT predictions, churn risk
│   ├── placement.py      # adaptive placement test
│   ├── glossary.py       # bilingual glossary by track
│   ├── duels.py          # async 1v1 duels (challenge, join, answer, result)
│   ├── exams.py          # timed certification mock exam + per-domain report
│   ├── tutor.py          # Groq explanations + BM25 RAG context
│   ├── content.py        # tracks, author agent, QA agent, duplicates, versioned edits
│   ├── billing.py        # Stripe checkout, webhook, subscription state
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

1807 questions across 8 tracks / 226 skills, every one with a canonical `source`;
70 bilingual glossary terms. Track 8 is the AWS Cloud Practitioner certification
(300 questions, 19 skills, 4 official domains). 111 questions are executable
(`fill_blank_exec` / `fix_bug`) and their expected stdout is verified in CI by
actually running the reference code in CPython.

Questions are versioned: `Question.content_version` bumps on edit and
`Response.question_version` stamps the version answered, so correcting a question
never rewrites history.

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
