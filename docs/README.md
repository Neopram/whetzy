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
| Desplegar (Cloudflare y Railway, ambos automáticos desde `master`), migrar, backup/restore, diagnosticar | `RUNBOOK.md`, `RELEASE.md` |
| Entender el sistema | `ARCHITECTURE.md`, `API.md`, `DECISIONS.md` |
| Ver la posición frente a la competencia, con pesos fijos (última: §12, captura en vivo 2026-09-24, sin re-puntuar) | `competitive-teardown.md` |
| Historia narrativa por sesión | `STATUS.md`, `CHANGELOG.md` |
| Tiendas (listing, privacidad, checklist de Apple 4.8 / 3.1.1) | `store/` |
| Verificar cualquier afirmación, cerrar una tarea sin errores, correr la verificación masiva (Serie 20), elegir modelo y ahorrar tokens | **`PROTOCOLO_VERIFICACION.md`** |
| Plan de distribución masiva ES + EN (canales, cadencia, herramientas $0, KPIs) | **`DISTRIBUCION.md`** |
| Los 6 segmentos de usuario (Estudiante, Career-switcher, Developer Senior, Profesor, Empresa, Developer Web3/Solana) con personas, flujos y créditos por segmento | **`SEGMENTOS.md`** |
| Competencia directa e indirecta: precios verificados con URL y fecha, lógica de negocio del mercado y qué se adopta (§A, 2026-09-24) | **`COMPETENCIA.md`** |
| Spec del marketplace de instructores: revenue share 80/20 (ADR-41), quality gate, moderación | **`MARKETPLACE.md`** |
| Economía cerrada: créditos, referidos, códigos autogenerados, USDC como rail, credenciales verificables — y por qué **no hay token** (ADR-33) | **`ECONOMIA.md`** |
| Análisis de negocio de la sesión bf (competencia, ingresos, coste) — **no normativo**, con errata | `analisis-estrategico/` |
| Qué se construyó de verdad en los 12 primeros días, qué estaba marcado `DONE` sin estarlo, qué bloquea (nada de ello código) y qué objetivo es alcanzable | **`BALANCE-12-DIAS.md`** |
| Qué ve alguien que audita el sistema desde fuera sin fiarse de ningún doc: producción medida en vivo, CI, coste de contexto, y por qué no se usa NotebookLM ni Obsidian (ADR-40) | **`AUDITORIA_EXTERNA_2026-09-19.md`** |

Esos son los **dieciocho documentos vivos** (más `store/`). `analisis-estrategico/` y
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
python scripts/ledger.py check                # el ledger sigue siendo legible por máquina
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

`git push origin master` **despliega los dos**: el backend en Railway (verificado
2026-09-16) y el frontend en Cloudflare Pages, que está conectado a Git (verificado
2026-09-24: tras `5be177f`, `whetzy.com/landing/` sirve el hero nuevo). Wrangler a mano
sigue valiendo (RUNBOOK §1). Después, `node frontend/scripts/check-deployed.mjs` en PASS.
