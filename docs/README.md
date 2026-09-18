# Whetzy — Índice de documentación

Whetzy es una escuela bilingüe (ES/EN) de informática con motor adaptativo
(BKT · FSRS · Elo · bandit · DKT), ejecución de código en el navegador (Python,
SQL, JavaScript) y preparación de certificaciones. Backend: monolito FastAPI + PostgreSQL.
Frontend: React + Capacitor.

## Qué leer, según lo que vengas a hacer

| Quieres… | Lee |
|---|---|
| Saber qué construye Whetzy y qué falta (tracks, certs, fuentes, coste) | **`CATALOGO_MAESTRO.md`** |
| Saber qué está hecho, qué está en curso y qué bloquea el humano | **`AUTONOMOUS_STATE.md`** (ledger; fuente de verdad) |
| Operar una sesión autónoma | `ORCHESTRATOR.md` + `../CLAUDE.md` |
| Saber qué fuentes se pueden usar (solo gratuitas y legales) y cómo | **`CATALOGO_MAESTRO.md` §2.1** + `DECISIONS.md` ADR-11 |
| Desplegar (Cloudflare con wrangler, Railway automático), migrar, backup/restore, diagnosticar | `RUNBOOK.md`, `RELEASE.md` |
| Entender el sistema | `ARCHITECTURE.md`, `API.md`, `DECISIONS.md` |
| Ver la posición frente a la competencia, con pesos fijos (última: §11, Educative y los 3 canales) | `competitive-teardown.md` |
| Historia narrativa por sesión | `STATUS.md`, `CHANGELOG.md` |
| Tiendas (listing, privacidad, checklist de Apple 4.8 / 3.1.1) | `store/` |
| Verificar cualquier afirmación, cerrar una tarea sin errores, correr la verificación masiva (Serie 20), elegir modelo y ahorrar tokens | **`PROTOCOLO_VERIFICACION.md`** |
| Análisis de negocio de la sesión bf (competencia, ingresos, coste) — **no normativo**, con errata | `analisis-estrategico/` |

Esos son los **once documentos vivos** (más `store/`). `analisis-estrategico/` y
`legal/` (raíz) no mandan sobre el código. Todo lo demás está en
`archive/` — incluida la estrategia v3 del dueño, superada por el catálogo — y **no
manda**: si algo de `archive/` contradice a un documento vivo, gana el vivo.

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
2026-09-16). El frontend en Cloudflare Pages se despliega a mano con
`npx wrangler pages deploy dist --project-name whetzy --branch main` desde
`frontend/` (RUNBOOK §1; H.11 cerrado el 2026-09-18).
