# Whetzy — Operations Runbook

## Deploy to Cloudflare Pages (frontend)

**Deploy is MANUAL** — no Git connection in Cloudflare Pages. Run from `frontend/`:

```bash
npm run build
npx wrangler pages deploy dist --project-name whetzy --branch main
```

First time per machine requires `npx wrangler login` (opens browser OAuth). The `--branch main` flag sends it to Production (whetzy.com). Verified 2026-09-18 (H.11 closed, sesión bc): 153 files, deploy `8c077b9a.whetzy.pages.dev`.

---

## Deploy to Railway (backend)

**Deploy is AUTOMATIC** — Railway deploys from `master` automatically (verified 2026-09-16, H.16). After `git push origin master`, Railway runs migrations and content_loader without manual intervention.

To monitor deployment:
1. Check Railway dashboard for build status
2. Verify: `curl https://api-production-9751.up.railway.app/health`

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
   list **71** paths.
5. In the deploy logs, confirm `start.sh` got through all four stages:
   `alembic upgrade head` → `content loaded` → `gamification seeded` →
   `launching gunicorn`. Content load should report **0 skipped** questions;
   if it exits with code 1, a JSON file has a syntax error or references an
   unknown skill_id — check the deploy log for the traceback.

**Note on question count:** the bank grows over time. Verify the loaded count
matches `check_question_bank.py` output (currently 6233), not a hardcoded
number. Any non-zero `skipped` count means a question references a skill_id
that does not exist in `curriculum/tracks.json`.

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

Current Alembic HEAD: `t0u1v2w3x4y5` (20 migrations, single head — verified 2026-09-18)
Chain: `<base> → a1b2 → … → r8s9t0u1v2w3 → s9t0u1v2w3x4 → t0u1v2w3x4y5`

Always recompute — never trust this line:

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

No external services needed. 739+ tests against SQLite in-memory (Alembic migrations are Postgres-only; tests use `Base.metadata.create_all` on SQLite).

## Load question bank (dev)

```bash
cd backend
python -m app.services.content_loader   # loads questions from content/questions/**/*.json
```

This is the same command `start.sh` runs at every deploy. It is idempotent — safe
to run multiple times. In prod, a new deploy automatically re-runs it.
To see how many questions loaded: check the log line `questions loaded`.

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
| RAG not used (`grounded=false`) | BM25 index not built yet — it starts async in `main.py`; check logs for `rag_ready` |
| Rate limit 429 in tests | Each test must use a unique X-Forwarded-For header |
| Alembic error "target database is not up to date" | Run `alembic upgrade head` |

## Rollback a bad deploy

1. In Railway: Deployments → click the last-good deploy → "Redeploy"
2. If migration was applied: `alembic downgrade -1` against the prod DB (needs direct DB access)

## DB backup / restore

Scripts (all read `PGPASSWORD`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_NAME` from the
environment; defaults match the local Docker DB):

| Script | Purpose |
|---|---|
| `scripts/db_backup.sh [out.dump]` | Dump the DB to a compressed custom-format file (`backups/neurium_YYYYMMDD_HHMMSS.dump`) |
| `scripts/db_restore.sh <file> [db]` | Restore into an existing (empty) database; filters the benign `transaction_timeout` warning from `pg_dump ≥ 17` against `pg16` and verifies `users` exists |
| `scripts/db_restore_test.sh [file]` | Backup → restore into a temp DB → row-parity check → cleanup (`trap cleanup EXIT`, also on failure) |

```bash
# Local: backup, and a full restore smoke test
PGPASSWORD=neurium_dev ./scripts/db_backup.sh
PGPASSWORD=neurium_dev ./scripts/db_restore_test.sh

# Production (Railway): tunnel with the CLI, then dump
railway connect --service whetzy-db
DB_HOST=localhost DB_PORT=5432 PGPASSWORD=<railway-password> \
  ./scripts/db_backup.sh backups/prod_$(date +%Y%m%d).dump

# Restore into a fresh local DB
PGPASSWORD=neurium_dev createdb --host=localhost --port=5433 --username=neurium neurium_recovery
PGPASSWORD=neurium_dev ./scripts/db_restore.sh backups/<file>.dump neurium_recovery
```

**Before a production migration**: take a `pre_migration_<ts>.dump` first. Since
`git push origin master` deploys and runs `alembic upgrade head` automatically, do
the backup *before* the push. Store production backups off-machine; never commit them.

Recovery: pick the last clean dump (`ls -lht backups/`) → `createdb` an empty target →
`db_restore.sh` → point `DATABASE_URL` at it → `GET /health/ready` → `db_restore_test.sh <dump>`
for row parity → swap traffic. Last full test: 2026-09-08 (7 tracks / 1253 questions
at the time, < 5 s from a 544 KB dump); the scripts have not changed since.
