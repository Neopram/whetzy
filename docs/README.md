# Whetzy — Backend Documentation

Whetzy is an adaptive learning platform for Python + data engineering. The backend is a FastAPI monolith backed by PostgreSQL, providing a REST API consumed by the React/Capacitor frontend.

## Quick start (local dev)

```bash
# 1. Start Postgres (Docker)
docker compose up -d

# 2. Install dependencies
cd backend && pip install -r requirements.txt

# 3. Copy env config
cp .env.example .env

# 4. Run migrations
alembic upgrade head

# 5. Load question bank
python -m app.scripts.content_loader

# 6. Start the API
uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

## Environment variables (key ones)

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | postgres at :5432 | Local Docker uses :5433 |
| `SECRET_KEY` | insecure dev key | **Change in production** |
| `GROQ_API_KEY` | — | Required for AI tutor |
| `EMAIL_PROVIDER` | `smtp` | `smtp` / `resend` / `log` |
| `SMTP_USER` / `SMTP_PASSWORD` | — | Required when EMAIL_PROVIDER=smtp |
| `RESEND_API_KEY` | — | Required when EMAIL_PROVIDER=resend |
| `FRONTEND_BASE_URL` | https://whetzy.com | Used in email links |

## Production URLs

| Surface | URL |
|---|---|
| API | https://api-production-9751.up.railway.app |
| Frontend | https://whetzy.com |
| OpenAPI | https://api-production-9751.up.railway.app/api/v1/openapi.json |

## Tests

```bash
cd backend
COVERAGE_FILE=C:\Temp\.coverage_whetzy python -m pytest tests/ --tb=short
```

229 tests (134 unit + 95 integration) running against SQLite in-memory. No external services required.

## Key files

| File | Purpose |
|---|---|
| `docs/ARCHITECTURE.md` | System design and component overview |
| `docs/API.md` | API conventions and key endpoints |
| `docs/RUNBOOK.md` | Deploy, migrate, rollback, troubleshoot |
| `docs/DECISIONS.md` | Architecture decision log |
| `docs/AUTONOMOUS_STATE.md` | Task backlog and progress ledger |
| `docs/STATUS.md` | Honest status report per phase |
