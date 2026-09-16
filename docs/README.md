# Whetzy — Índice de documentación

Whetzy es una escuela bilingüe (ES/EN) de informática con motor adaptativo
(BKT · FSRS · Elo · bandit · DKT), ejecución de código en el navegador (Python,
SQL) y preparación de certificaciones. Backend: monolito FastAPI + PostgreSQL.
Frontend: React + Capacitor.

## Qué leer, según lo que vengas a hacer

| Quieres… | Lee |
|---|---|
| Saber qué construye Whetzy y qué falta (tracks, certs, fuentes, coste) | **`CATALOGO_MAESTRO.md`** |
| Saber qué está hecho, qué está en curso y qué bloquea el humano | **`AUTONOMOUS_STATE.md`** (ledger; fuente de verdad) |
| Operar una sesión autónoma | `ORCHESTRATOR.md` + `../CLAUDE.md` |
| Desplegar, migrar, restaurar, diagnosticar | `RUNBOOK.md`, `runbook_db_backup_restore.md`, `RELEASE.md` |
| Entender el sistema | `ARCHITECTURE.md`, `API.md`, `DECISIONS.md` |
| Ver la posición frente a la competencia, con pesos fijos | `competitive-teardown.md` |
| Leer la estrategia del dueño (con su adenda de 2026-09-16) | `whetzy_estrategia_definitiva_v3.md` |
| Historia narrativa por fase | `STATUS.md`, `CHANGELOG.md` |
| Tiendas (listing, privacidad, iconos) | `store/` |

## Arranque local

```bash
docker compose up -d                          # Postgres en :5433
cd backend && pip install -r requirements.txt
cp .env.example .env
python -m alembic upgrade head
python -m app.services.content_loader         # carga tracks, preguntas, glosario y lecciones
uvicorn app.main:app --reload                 # http://localhost:8000/api/v1/openapi.json
```

## Verificación — los comandos que sostienen cada número de los docs

```bash
python scripts/check_question_bank.py         # banco: ids, idiomas, opciones, sesgo, ratio ejecutable
python scripts/check_docs.py                  # docs y /evidence coinciden con el contenido y Alembic
cd backend && python -m pytest tests/content  # lecciones, ejecutables, sql_exec, tildes, blueprints
cd backend && python -m pytest -q             # suite completa
cd frontend && npx tsc -b --force && npx vitest run && npm run build
```

Un número en un doc sin uno de estos comandos detrás es un bug. Las cifras del
banco viven en la fila `Contenido` de `AUTONOMOUS_STATE.md` y en
`CATALOGO_MAESTRO.md` §1, y `check_docs.py` falla si divergen del código.

## URLs de producción

| Superficie | URL |
|---|---|
| API | https://api-production-9751.up.railway.app |
| Frontend | https://whetzy.com |
| OpenAPI | https://api-production-9751.up.railway.app/api/v1/openapi.json |

`git push origin master` **despliega** el backend (Railway, auto-deploy verificado
2026-09-16). El frontend en Cloudflare Pages se redespliega a mano (H.11).
