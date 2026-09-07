# Whetzy

> **El motor que te aprende mientras aprendes.** / *The engine that learns you while you learn.*

Adaptive learning platform that takes a learner from basic Python to employable AI
Engineer. Bilingual (ES/EN, natively authored). A layered adaptive engine
(FSRS-6 + Elo + BKT + Thompson-sampling bandit, DKT planned) selects the next
question that maximizes learning, gated by mastery-verified prerequisites.

## Stack
- **Frontend:** React + TypeScript + Vite (PWA, Capacitor-ready). Light-first, sky-blue identity.
- **Backend:** FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + Redis.
- **AI tutor:** Groq/Llama 3 via a swappable `LLMProvider` (Claude later); grounded fallback when no key.
- **Security:** OWASP ASVS 5.0-aligned headers + per-IP rate limiting; Argon2/JWT-ready.

## Run locally (Docker)
```bash
cp .env.example .env      # then set a strong SECRET_KEY and POSTGRES_PASSWORD
docker compose up --build
# API on http://localhost:8000  (docs at /docs)
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
backend/    FastAPI app — engine/, services/, api/, models/, schemas/
frontend/   React PWA — pages/, components/, services/api.ts, stores/
content/    curriculum (tracks.json) + question bank + placement exam
legal/      privacy policy, terms of service
docker-compose.yml, .github/workflows/ci.yml, .env.example
```

## Status
See `docs/STATUS.md` for the honest, per-domain completion breakdown and the
competitive scorecard.

## License
Proprietary — © Whetzy.
