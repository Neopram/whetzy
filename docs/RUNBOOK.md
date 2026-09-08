# Whetzy — Operations Runbook

## Deploy to Railway (backend)

**Deploy is MANUAL** — no GitHub webhook active. After pushing code:

1. Log in to railway.app → select the Whetzy service
2. Click "Deploy" on the latest commit
3. Monitor logs for startup message: `Starting Whetzy (env=production ...)`
4. Verify: `curl https://api-production-9751.up.railway.app/health/ready`

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

Current Alembic HEAD: `d4e5f6a7b8c9`
Chain: `<base> → a1b2c3d4e5f6 → b2c3d4e5f6a7 → c3d4e5f6a7b8 → d4e5f6a7b8c9`

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
