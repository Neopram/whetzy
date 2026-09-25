# Whetzy — Operations Runbook

## Deploy to Cloudflare Pages (frontend)

**Correction 2026-09-24: Cloudflare Pages IS connected to Git.** Every push to a branch gets a preview build (the `cloudflare-workers-and-pages` bot comments the URL on the PR, e.g. `https://claude-trusting-franklin-2ww.whetzy.pages.dev` for PR #6) and a `Cloudflare Pages` check. Verified 2026-09-24 from the owner's build log: a push to `master` triggers the Production build, which runs `npx tsc -b && npx vite build` with a dashboard variable `VITE_API_URL=https://whetzy.com` — the origin of the login 405. Since then the build no longer depends on either: `vite.config.ts` takes `VITE_API_URL` **only** from `frontend/.env.production` (a different env value is ignored with a `[require-api-url] Ignorando…` warning in the log) and pre-renders the landing inside any `vite build`. Deleting that dashboard variable is still recommended so nobody is misled by it. Manual deploy still works, from `frontend/`:

```bash
npm run build
npx wrangler pages deploy dist --project-name whetzy --branch main
```

Then, **always**:

```bash
node scripts/check-deployed.mjs   # must print PASS for https://whetzy.com
```

A deploy is not done until that passes. On 2026-09-24 the page loaded fine while login was dead: the bundle had `https://whetzy.com` as its API (405 on login) and a Pages Function answered 200 "Autenticado correctamente" to any POST on `/api/*`. Two checks now catch exactly that (ledger 30.0). The API origin lives in `frontend/.env.production` and `vite.config.ts` refuses to build if it is the frontend's own domain or does not end in `/api/v1`.

First time per machine requires `npx wrangler login` (opens browser OAuth). The `--branch main` flag sends it to Production (whetzy.com). Verified 2026-09-18 (H.11 closed, sesión bc): 153 files, deploy `8c077b9a.whetzy.pages.dev`.

---

## Deploy to Railway (backend)

**Deploy is AUTOMATIC** — Railway deploys from `master` automatically (verified 2026-09-16, H.16). After a commit reaches `master` (the owner merges, ADR-45), Railway runs migrations and content_loader without manual intervention.

To monitor deployment:
1. Check Railway dashboard for build status
2. Run the post-deploy smoke tests:
   ```bash
   ./scripts/smoke_post_deploy.sh
   # With QA login (optional):
   QA_EMAIL=qa@example.com QA_PASSWORD=secret ./scripts/smoke_post_deploy.sh
   ```
   The script checks `/health/ready`, OpenAPI, auth, tracks, latency, and
   optionally logs in with a QA account to verify `/quiz/start` end-to-end.
   A deploy is not done until it prints `RESULT: PASS`.

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
RESEND_API_KEY=<key>         # basta esta para que el correo salga
EMAIL_FROM_ADDRESS=noreply@whetzy.com
FRONTEND_BASE_URL=https://whetzy.com
OWNER_EMAIL=<tu email>        # cuenta de dueño (rol owner); ver «Cuenta de dueño»
OWNER_PASSWORD=<≥ 12 caracteres, solo aquí>
# EMAIL_PROVIDER=auto        # por defecto; solo para forzar smtp|resend|log
# SMTP_USER=... SMTP_PASSWORD=...   # alternativa a Resend (hacen falta las dos)
```

### Cuenta de dueño (acceso a `/admin`)

`scripts/start.sh` corre `python -m app.services.bootstrap_owner` en cada arranque.
Con `OWNER_EMAIL` y `OWNER_PASSWORD` en las variables de Railway crea esa cuenta, o
la actualiza: rol `owner`, email verificado y **esa** contraseña. Cambiar la variable
y redesplegar cambia la contraseña. Con las dos vacías no hace nada; con una sola, el
arranque falla a propósito. El log dice `[owner] created|updated|unchanged: <email>`,
nunca la contraseña.

Historia (2026-09-24): hasta entonces la cuenta `admin@whetzy.com` la insertaba la
migración `20260922_setup_admin` con un hash **versionado en el repo** y rol
`superuser`, que `/admin` rechaza con 403. `20260924_owner_role` pasa ese rol a
`owner` y anula el hash filtrado (queda sin contraseña hasta que `OWNER_*` la fije).

### Qué hace el arranque, y por qué falla en vez de seguir

`alembic upgrade head` → `content_loader` → `bootstrap_owner` son **fatales**; el seed
de gamificación no. Entre el 2026-09-22 y el 2026-09-24 el script seguía adelante
aunque todo fallara y `content_loader` ni se ejecutaba: producción arrancó con los 18
tracks vacíos («Track not found») y `/health` decía 200. Probado en local contra
Postgres 16: base vacía → 18 tracks, 6.305 preguntas y 622 términos en ~10 s;
`CONTENT_DIR` roto → `exit 1` y gunicorn no arranca.

### Correo: la variable que no se puede olvidar (H.30)

Sin proveedor, la verificación de cuenta y el reset de contraseña **se escriben
en el log del contenedor y se pierden**, mientras la pantalla dice que el enlace
se ha enviado. Quien olvide su contraseña pierde la cuenta. Estuvo así en
producción hasta el 2026-09-20.

El proveedor se deduce de las credenciales: **basta `RESEND_API_KEY`**. No hace
falta tocar `EMAIL_PROVIDER` (antes sí, y acertar solo una de las dos no servía
de nada, en silencio).

1. Crear cuenta en [resend.com](https://resend.com) — capa gratis: 3.000
   correos/mes, 100/día. Suficiente para la beta.
2. Verificar el dominio `whetzy.com` (añadir los registros DNS que indica, en
   Cloudflare). **Mientras no esté verificado**, Resend solo deja enviar desde
   `onboarding@resend.dev`: poner `EMAIL_FROM_ADDRESS=onboarding@resend.dev`
   temporalmente.
3. En Railway → Variables: `RESEND_API_KEY=re_...`. El contenedor se reinicia.
4. **Comprobarlo, no suponerlo:**

```bash
TOKEN=<token de una cuenta con role=owner>
API=https://api-production-9751.up.railway.app/api/v1
curl -s -H "Authorization: Bearer $TOKEN" $API/admin/email/status
curl -s -X POST -H "Authorization: Bearer $TOKEN" $API/admin/email/test
```

`status` debe decir `"configured": true`; `test` envía un correo real a la
dirección del owner y devuelve 503 **con el motivo** si el proveedor lo rechaza
(clave inválida, dominio sin verificar). En los logs de arranque:
`Email: proveedor resend, remitente ...`, o `email_not_configured` si falta.

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
a merge into `master` deploys and runs `alembic upgrade head` automatically, do
the backup *before* the owner merges. Store production backups off-machine; never commit them.

Recovery: pick the last clean dump (`ls -lht backups/`) → `createdb` an empty target →
`db_restore.sh` → point `DATABASE_URL` at it → `GET /health/ready` → `db_restore_test.sh <dump>`
for row parity → swap traffic. Last full test: 2026-09-08 (7 tracks / 1253 questions
at the time, < 5 s from a 544 KB dump); the scripts have not changed since.

---

## Service Level Objectives (SLO) — 33.0

| SLO | Target | Prometheus metric | Window | Status |
|-----|--------|-------------------|--------|--------|
| API availability | ≥ 99.5 % | `http_requests_total{status!~"5.."}` / `http_requests_total` | 30 days rolling | **measured** — ratio of non-5xx to total requests |
| Quiz latency (p95) | < 500 ms | `http_request_duration_seconds{path="/api/v1/quiz/answer"}` (histogram_quantile 0.95) | 30 days rolling | **measured** — `/quiz/start` and `/quiz/answer` both instrumented |
| Health/ready latency (p95) | < 500 ms | — | — | **sin medir** — `/health*` excluded from metrics middleware (`_SKIP_PREFIXES`) to avoid cardinality explosion; manual checks only |
| RPO (Recovery Point Objective) | ≤ 24 h | — | — | **sin medir** — Railway Postgres daily backups assumed; no Prometheus metric; verify backup age via Railway dashboard |
| RTO (Recovery Time Objective) | ≤ 60 min | — | — | **sin medir** — recovery is manual (`db_restore.sh`); no automated measurement; monthly drill (`db_restore_test.sh`) validates the procedure |

### Alerting

No Prometheus alerting is configured. Railway provides basic uptime monitoring.
When Prometheus/Grafana is set up, add these rules:

```yaml
# Availability drops below 99.5% over 1 hour
- alert: APIAvailabilityLow
  expr: (sum(rate(http_requests_total{status!~"5.."}[1h])) / sum(rate(http_requests_total[1h]))) < 0.995

# Quiz p95 latency exceeds 500ms over 5 minutes
- alert: QuizLatencyHigh
  expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{path=~"/api/v1/quiz/.*"}[5m])) by (le)) > 0.5
```

### Monthly restoration drill

Run `scripts/db_restore_test.sh` against the latest backup once per month.
The script dumps the current DB, restores to a recovery database, compares
row counts per table, and reports PASS/FAIL. A truncated dump must produce
FAIL (the script validates this). Log the result in `docs/restore_log.md`.
