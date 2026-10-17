# Whetzy

> **El motor que te aprende mientras aprendes.** / *The engine that learns you while you learn.*

Bilingual (ES/EN, natively authored) school of computing: Python, software
engineering, AI/ML, SQL, cybersecurity, cloud certifications. A layered adaptive
engine (BKT + FSRS + Elo, DKT with fallback; Thompson sampling only in the placement
test) picks the skill by mastery and the question by Elo, gated by mastery-verified prerequisites. Code
runs in the browser (Python via Pyodide, SQL via sql.js, JavaScript in a Worker
sandbox) — no execution server.

## Stack
- **Frontend:** React + TypeScript + Vite (PWA, Capacitor). Light-first, sky-blue identity. Hosted on Cloudflare Pages (`whetzy.com`).
- **Backend:** FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL on Railway (auto-deploy from `master`).
- **AI tutor:** Groq `qwen/qwen3.8-27b` behind a swappable `LLMProvider`, grounded with an in-memory BM25 index; grounded fallback when no key.
- **Security:** OWASP ASVS 5.0-aligned headers + per-IP rate limiting; JWT access/refresh; GDPR export + delete.
- **Content:** every question cites a source; sources are free and legally reusable or cited only (ADR-11).

## Run locally (Docker)
```bash
cp .env.example .env      # then set a strong SECRET_KEY and POSTGRES_PASSWORD
docker compose up --build
# API on http://localhost:8000  (OpenAPI at /api/v1/openapi.json)
```
The API boots, ingests `content/` and seeds gamification automatically.

## Run locally (without Docker)
Backend (Python 3.12):
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # see note below on Windows
pip install -r requirements.txt aiosqlite
# minimal .env: ENVIRONMENT=development, DATABASE_URL=sqlite+aiosqlite:///./neurium_dev.db, SECRET_KEY=...
python -m app.services.content_loader   # load the question bank
python -m app.services.seed             # seed leagues/missions/badges
uvicorn app.main:app --reload
```
Frontend:
```bash
cd frontend
npm install
npm run dev     # Vite proxies /api -> http://127.0.0.1:8000 (see vite.config.ts)
```
> Windows note: `python -m venv` can fail in paths containing spaces; create the venv
> in a space-free directory. SQLite needs an **absolute** `DATABASE_URL` path.

## Repository layout
```
backend/    FastAPI app — services/ (engine/ inside), api/, models/, schemas/
frontend/   React PWA — pages/, components/, services/api.ts, stores/
content/    curriculum (tracks.json) + questions + lessons + glossary + placement exam
docs/       ledger (AUTONOMOUS_STATE.md), catalog, runbook, ADRs, competitive teardown
docker-compose.yml, .github/workflows/ci.yml, .env.example
```

## Status
Start at `docs/README.md`. The source of truth for progress and human blockers is
`docs/AUTONOMOUS_STATE.md`; the scope is `docs/CATALOGO_MAESTRO.md`; the honest
competitive position (fixed weights, latest recalculation in §14) is
`docs/competitive-teardown.md`. `docs/STATUS.md` is a historical per-session log.

## License
Code: proprietary, all rights reserved. Original educational content in `content/`: CC BY-NC-ND 4.0 (`LICENSE` §2). Third-party material keeps its own licence (`content/sources/index.json`). Details in [`LICENSE`](LICENSE).
