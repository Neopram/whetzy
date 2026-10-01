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

## Prueba de arranque y de build web (obligatorias antes de push, desde 2026-09-26)

**Por qué.** El 2026-09-26 `ec97405` llegó a `master` con contenido que el loader no sabía leer. `start.sh` corre con `set -e`, el contenedor murió antes de gunicorn y la API dio 502 de 09:35 a 10:48 UTC (logs de Railway, deploy `620edcd3`: `KeyError: 'order'` en bucle). Los recuentos de `check_docs` estaban en verde: contar no es cargar. El mismo día, el build de Cloudflare Pages falló en Node 20.19 (`navigator is not defined`) mientras en local, con Node 22, pasaba.

**Arranque (content/ o backend/).** Sin Docker, con Postgres 16 del sistema:

```bash
D=/var/tmp/pgw; mkdir -p $D && chown postgres $D
su postgres -c "/usr/lib/postgresql/16/bin/initdb -D $D/data -A trust -U postgres"
su postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D $D/data -o '-p 5433 -k /tmp' -l $D/log start"
psql -h /tmp -p 5433 -U postgres -c "create user neurium with password 'neurium_dev' superuser;" -c "create database neurium owner neurium;"
cd backend && export DATABASE_URL=postgresql+asyncpg://neurium:neurium_dev@localhost:5433/neurium SECRET_KEY=x ENVIRONMENT=development OWNER_EMAIL=owner@example.test OWNER_PASSWORD='Local-test-pass-123!'
alembic upgrade head && python -m app.services.content_loader && python -m app.services.bootstrap_owner && python -m app.services.seed
```

Después `gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8765` y `/health` = 200. No pongas la base en un directorio cuyos permisos puedan cambiar (el scratchpad de una sesión): Postgres se cae.

**Build web (frontend/).** Checkout limpio (`git worktree add`), `npm ci` y el build con la versión de `.nvmrc`:

```bash
npx -y -p node@20.19.0 -- sh -c 'node node_modules/typescript/bin/tsc -b && node node_modules/vite/bin/vite.js build'
```

Tiene que existir `dist/landing/index.html` con `data-lcp="hero"`. Un `node_modules/` o `dist/` viejos esconden fallos (dependabot subió `@vitejs/plugin-react` a 6.x, que exige Vite 8, y pyodide a 314.x, sin `pyodide.asm.js`).

**Verificar un despliegue.** Conector Railway: `list-deployments` (último en `SUCCESS`) y `get-logs` con filtro `"[start]" OR "[owner]" OR "Content loaded" OR "Traceback"`; luego `node frontend/scripts/check-deployed.mjs` (desde `frontend/`).

## Contenido reescrito por agentes (desde 2026-09-26)

**Herramientas** en `scripts/content_qa/` (tabla en su README). Se ejecutan desde la raíz del repo y los agentes no las editan: el 26-09 un agente sobrescribió el validador del scratchpad.

**Proceso por lote**, sin excepciones:

1. **Escritor** Haiku 4.5 (ADR-52; hasta el 2026-09-26, Sonnet) por fichero (o 10 lecciones) que escribe solo en el scratchpad, nunca en el repo.
2. **Revisor** Sonnet 5 distinto, que revisa **todas** las piezas, que no escribe y devuelve problemas con la corrección.
3. **Corrector** Sonnet 5 que aplica la revisión y vuelve a validar.
4. **Comprobación propia** antes de copiar al repo:
   - `validate_lessons.py` en OK;
   - `check_key_drift.py` y `check_expl_key.py` sin sospechosos sin explicar. Son sospechas, no veredictos: se leen una a una;
   - `check_only_fields.py --fields ...` si el encargo era tocar solo unos campos;
   - `check_urls.py` sin fallos. Un 403 se abre a mano con WebFetch;
   - lectura de al menos dos piezas enteras.
5. `pytest tests/content`, prueba de arranque de arriba y un commit por track.

**Fallos observados, cada uno con su defensa:**

- **Haiku** escribió lecciones con relleno sin sentido y errores técnicos (7 de 10 en el piloto de track28). Por eso la enmienda a ADR-50 pasó la autoría a Sonnet; ADR-52 (2026-09-27, dueño) la devuelve a Haiku con revisión completa de Sonnet 5 y un piloto de 10 ítems: más de 3 con `blocker`/`major` para el bloque y lo decide el dueño.
- **El reescritor movió la clave** a otra ranura (track28, track29, `mod3002` entero) y dijo «todo correcto». Defensa: `check_key_drift.py`. Si una posición del repo rota 0,1,2,3…, `rebalance_positions.py`.
- **Los agentes inventan URLs** (404 en las lecciones NoSQL de track27) y copian datos personales del contexto (el correo del dueño en `l260101`). Defensas: `check_urls.py` y `test_no_personal_data.py`. Los ejemplos usan `ada@example.com`.
- **No se toca un fichero que un workflow está leyendo**: un `git stash` a mitad cambió la base de un agente y su salida mezcló dos versiones.
- **`content_loader` nunca borra preguntas**: se arregla en su sitio sin renombrar ids; un id nuevo deja la vieja viva en producción.
- **Lecciones SQL**: el test las ejecuta con SQLite, así que no se usa sintaxis solo de PostgreSQL en el ejemplo (o se explica en el texto sin ejecutarla).
- **`logging` escribe en stderr**: no cuenta como salida del ejemplo; `logging.basicConfig(stream=sys.stdout)` si la salida es parte de la lección.

- **Los revisores también fallan en las dos direcciones** (noche del 26-09): dejaron pasar que un /24 de Google Cloud da 254 IP utilizables (son 252: Google reserva las dos primeras y las dos últimas) y tacharon de «inventada» una frase que está literal en `docs.python.org/3/library/exceptions.html`. Defensa: la lectura propia de al menos dos piezas por lote no es opcional, y cualquier cifra de nube se contrasta con la página oficial.
- **Opciones de preguntas (39.28): parche, no fichero.** El agente escribe `qpatch/<track>/<módulo>.pN.json` con solo `options_es`/`options_en` de las preguntas que toca; un script lo aplica sobre la copia original y lo comprueba (coletillas, número de opciones, repetidas, clave movida por similitud, correcta más larga). Así no puede cambiar ids, claves ni explicaciones aunque quiera. Las claves falsas que aparezcan se corrigen aparte, a mano y con la fuente abierta, después de aplicar los parches.
- **El límite de uso de la cuenta mata a los subagentes a mitad** (26-09, 20:20 UTC): los workflows devuelven `null` por agente. Se reanudan con `resumeFromRunId` y los mismos `args`: lo terminado sale de caché y lo cortado se repite desde el principio (sobrescribe sus ficheros a medias). No lances más de 6-7 workflows a la vez.
- **Coletillas: la lista no está cerrada.** La tercera familia salió minando el banco (colas de 2-6 palabras frecuentes en incorrectas y casi nunca en correctas). Antes de dar un track por limpio, repite esa minería; la guarda solo ve lo que conoce.

## Suite backend: tiempos y entorno (26-09)

- La suite sin `tests/content` tarda ~37 min en este contenedor; ~28 min son de `tests/integration/test_rag_self_retrieval.py::test_index_memory_bounded_and_hits_self_retrieval_bar`, cuadrático en el tamaño del banco (11 000 preguntas × 2 idiomas × 12 000 documentos). No está colgada: `py-spy dump --pid N` lo muestra en `rag.py:190`.
- En un contenedor nuevo: `SETUPTOOLS_USE_DISTUTILS=stdlib pip install http-ece` antes de `pip install -r requirements.txt`, y `pip install --ignore-installed cryptography` si pip no puede desinstalar la de Debian.
- El hook exige la ruff de CI (0.16.8). Si el PATH trae otra antes (`/root/.local/bin`), empuja con `PATH=/usr/local/bin:$PATH git push`.
- Playwright con el Chromium preinstalado de otra versión: un `playwright.sandbox.config.ts` local (sin commitear) que herede de `playwright.config.ts` y ponga `launchOptions.executablePath` a `/opt/pw-browsers/chromium-*/chrome-linux/chrome`.

## LLM: techo diario y respaldo (39.11, 39.12)

- `LLM_DAILY_CALL_LIMIT` (por defecto 2000): llamadas al LLM por día UTC **y por proceso** (Railway corre 2 workers de gunicorn y no hay Redis: el techo real es el doble). Al superarlo el tutor responde con el contexto de la pregunta y el log dice `llm_daily_budget_exhausted`. `0` = sin techo.
- `LLM_FALLBACK_BASE_URL`, `LLM_FALLBACK_API_KEY`, `LLM_FALLBACK_MODEL`: proveedor compatible con OpenAI que entra si Groq da timeout, error de red, 5xx o 429. Vacíos = sin respaldo; entonces se responde con el contexto. Un 4xx distinto de 429 (clave mala, petición mal formada) **no** se esconde.
- El campo `provider` de `POST /tutor/explain` dice quién respondió: `groq`, `fallback-llm` o `fallback` (contexto).

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

Current Alembic HEAD: `20261001_granted_tier` (48 migrations, single head — verified 2026-10-01 with
`alembic heads` and `ls backend/alembic/versions/*.py | wc -l`; until then this line said
`t0u1v2w3x4y5`, 20 migrations, from 2026-09-18)

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
for row parity → swap traffic. Last full test: **2026-09-26** on the full catalogue (35 tracks, 177 modules, 723 skills): all tables match and a truncated dump is rejected (`docs/restore_log.md`). The three scripts were `100644` in git and failed with "Permission denied" when chained; now executable. Dumps (`backups/*.dump`) are git-ignored.

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

## Incident Management (22.7)

### Severity Levels

| Severity | Definition | Response time | Example |
|----------|-----------|---------------|---------|
| SEV-1 (Critical) | Service down, data loss risk, security breach | Immediate (< 15 min) | API returning 502, DB corruption, auth bypass |
| SEV-2 (Major) | Core feature broken, significant user impact | < 1 hour | Quiz flow broken, payments failing, login errors for subset of users |
| SEV-3 (Minor) | Non-core feature degraded, workaround exists | < 4 hours | Leaderboard stale, badge rendering broken, push notifications delayed |
| SEV-4 (Low) | Cosmetic issue, internal-only impact | Next business day | Admin panel typo, non-user-facing log noise, dev tooling broken |

### Escalation

Only the owner operates Whetzy (single-person team as of 2026-09-26):
1. Automated: Railway sends email on deploy failure or crash loop
2. Manual: owner monitors `GET /health/ready` and `/status` page
3. Runbook here is the single source of truth for recovery procedures

### Incident Response Checklist

1. **Acknowledge**: note the time and symptoms
2. **Classify**: assign severity (SEV-1 through SEV-4)
3. **Contain**: if SEV-1, immediately check Railway dashboard for crash/restart; check `/health/ready`
4. **Diagnose**: check deploy logs, `GET /admin/ops/errors`, `GET /admin/ops/health`
5. **Fix**: apply the fix, push to branch, merge via PR (ADR-45)
6. **Verify**: `scripts/smoke_post_deploy.sh` must PASS; `cd frontend && node scripts/check-deployed.mjs` must PASS
7. **Document**: fill in the postmortem template below

### Postmortem Template

```markdown
# Postmortem: [TITLE]

**Date**: YYYY-MM-DD
**Severity**: SEV-N
**Duration**: HH:MM (from detection to resolution)
**Author**: [name]

## Summary
One paragraph: what happened, who was affected, what was the impact.

## Timeline (UTC)
- HH:MM — First symptom detected
- HH:MM — Root cause identified
- HH:MM — Fix deployed
- HH:MM — Service confirmed healthy

## Root Cause
What broke and why. Be specific: commit hash, config change, external dependency.

## Impact
- Users affected: N (or %)
- Duration of degraded service: HH:MM
- Data loss: yes/no (describe if yes)

## Resolution
What was done to fix it. Link to the PR/commit.

## Lessons Learned
- What went well
- What went poorly
- Where we got lucky

## Action Items
| Action | Owner | Due | Status |
|--------|-------|-----|--------|
| [description] | [who] | [when] | TODO/DONE |
```

### Past Incidents

| Date | Severity | Title | Duration | Postmortem |
|------|----------|-------|----------|------------|
| 2026-09-18 | SEV-1 | Backend 502 for 2h30m (22.0) | 2h 30m | Recovery: redeployed with correct Alembic head |
| 2026-09-24 | SEV-1 | Login broken in production (30.0) | ~4h | Root cause: Cloudflare Pages dashboard variable overrode .env.production API URL |
