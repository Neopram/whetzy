# Whetzy — Operations Runbook

## Deploy to Railway (backend)

**Deploy is MANUAL** — no GitHub webhook active. After pushing code:

1. Log in to railway.app → select the Whetzy service
2. Click "Deploy" on the latest commit
3. Monitor logs for startup message: `Starting Whetzy (env=production ...)`
4. Verify: `curl https://api-production-9751.up.railway.app/health/ready`

### Recovering from "Application not found" (incident H.1)

`GET /health` returning `404 {"message":"Application not found"}` with the
header `x-railway-fallback: true` is **not** stale code. It means Railway has
no deployment behind the domain at all — the service is stopped, deleted, or
the domain was unlinked. No amount of pushing to `master` fixes it; the fix is
in the Railway dashboard.

1. railway.app → does the backend service still exist?
   - **Exists but stopped/crashed** → restart it, then read the deploy logs.
   - **Deleted** → recreate from the repo root `Dockerfile` (Railway must
     auto-detect Docker; if it falls back to Railpack the build fails).
   - **Exists and running but the domain 404s** → the domain is unlinked:
     re-attach `api-production-9751.up.railway.app` to the service.
2. Required env vars (see `.env.example`): `SECRET_KEY`, `DATABASE_URL`,
   `ENVIRONMENT=production`, `BACKEND_CORS_ORIGINS`. `GROQ_API_KEY` is
   optional — without it the tutor answers from the canonical explanation
   instead of the LLM, which degrades gracefully and does not block startup.
3. Deploy the latest `master`.
4. Verify, in this order:
   ```bash
   curl https://api-production-9751.up.railway.app/health
   curl -s https://api-production-9751.up.railway.app/api/v1/openapi.json | head -c 200
   ```
   `/health` must return `{"status":"healthy"}` and the OpenAPI document must
   list **57** paths.
5. In the deploy logs, confirm `start.sh` got through all four stages:
   `alembic upgrade head` → `content loaded` → `gamification seeded` →
   `launching gunicorn`. Content load should report **1507 questions, 0
   skipped**; anything else means the `content/` tree did not make it into the
   image.

**The startup path was smoke-tested end to end on 2026-09-13** against the
current `master`, running the real lifespan: 1507 questions / 0 skipped,
`/health` 200, 57 endpoints, BM25 RAG index built in 0.60 s with every
retrieved chunk carrying a `source`. The only dependency added since the last
successful deploy is `rank-bm25` (pure Python, no torch), which the existing
Dockerfile builds unchanged. So a redeploy is safe: if it fails, suspect the
Railway service or its env vars, not the code.

## DB migrations

```bash
# Never use Base.metadata.create_all in production.
# Generate a new migration:
cd backend
alembic revision --autogenerate -m "describe_the_change"

# Apply locally:
alembic upgrade head

# Check current revision:
alembic current

# Rollback one step:
alembic downgrade -1
```

Current Alembic HEAD: `m3n4o5p6q7r8` (13 migrations, single head — verified 2026-09-13)
Chain: `<base> → a1b2c3d4e5f6 → b2c3d4e5f6a7 → c3d4e5f6a7b8 → d4e5f6a7b8c9 → e5f6a7b8c9d0 → f6a7b8c9d0e1 → g7h8i9j0k1l2 → h8i9j0k1l2m3 → i9j0k1l2m3n4 → j0k1l2m3n4o5 → k1l2m3n4o5p6 → l2m3n4o5p6q7 → m3n4o5p6q7r8`

Don't trust this line — recompute it. It was stale by 9 migrations until
2026-09-13 because six schema changes landed without anyone updating it:

```bash
cd backend && alembic heads     # must print exactly ONE head
```

**First deploy to a DB with no alembic_version:** `start.sh` runs `alembic stamp head` before `upgrade head` to handle pre-existing schemas.

## Local DB (Docker)

```bash
docker compose up -d          # start postgres at :5433
docker compose down           # stop (data persists in volume)
docker compose down -v        # stop + wipe data
```

Connection: `postgresql+asyncpg://neurium:neurium_dev@localhost:5433/neurium`

## Run tests

```bash
cd backend
# Windows:
$env:COVERAGE_FILE = "C:\Temp\.coverage_whetzy"
python -m pytest tests/ --tb=short

# Linux/Mac:
COVERAGE_FILE=/tmp/.coverage_whetzy python -m pytest tests/ --tb=short
```

No external services needed. 229 tests against SQLite in-memory.

## Load question bank (dev)

```bash
cd backend
python -m app.scripts.content_loader   # loads 1253 questions from JSON fixtures
```

Only run in development. Production DB already has content.

## Environment variables (production checklist)

```bash
SECRET_KEY=<random 64 char hex>
DATABASE_URL=postgresql+asyncpg://<user>:<pass>@<host>/<db>
GROQ_API_KEY=<groq key>
ENVIRONMENT=production
DEBUG=false
EMAIL_PROVIDER=resend        # or smtp
RESEND_API_KEY=<key>         # if EMAIL_PROVIDER=resend
SMTP_USER=...                # if EMAIL_PROVIDER=smtp
SMTP_PASSWORD=...
EMAIL_FROM_ADDRESS=noreply@whetzy.com
FRONTEND_BASE_URL=https://whetzy.com
```

## Troubleshoot

| Symptom | Check |
|---|---|
| 503 on /health/ready | DB connection — check DATABASE_URL and pg is up |
| 401 on all requests | SECRET_KEY mismatch between instances |
| Email not sending | EMAIL_PROVIDER, SMTP_USER/RESEND_API_KEY, check logs for `email_failed` |
| AI tutor returns `provider=fallback` | GROQ_API_KEY not set or invalid |
| RAG not used (`grounded=false`) | ChromaDB index not built yet (starts async at startup) |
| Rate limit 429 in tests | Each test must use a unique X-Forwarded-For header |
| Alembic error "target database is not up to date" | Run `alembic upgrade head` |

## Rollback a bad deploy

1. In Railway: Deployments → click the last-good deploy → "Redeploy"
2. If migration was applied: `alembic downgrade -1` against the prod DB (needs direct DB access)
