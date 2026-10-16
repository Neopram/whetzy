# Whetzy — Índice de documentación

Whetzy es una escuela bilingüe (ES/EN) de informática con motor adaptativo
(BKT · FSRS · Elo · bandit · DKT), ejecución de código en el navegador (Python,
SQL, JavaScript) y preparación de certificaciones. Backend: monolito FastAPI + PostgreSQL.
Frontend: React + Capacitor.

## Qué leer, según lo que vengas a hacer

**Para empezar**

| Quieres… | Lee |
|---|---|
| Saber qué está hecho, qué está en curso y qué bloquea el humano | **`AUTONOMOUS_STATE.md`** (ledger; fuente de verdad; `python scripts/ledger.py next`) |
| Operar una sesión (rama + PR, sin `master`; ADR-45) | `ORCHESTRATOR.md`, **`PROMPT_CONTROL_TOTAL.md`** y `../CLAUDE.md` |
| Poner la documentación al día con el código antes de tocar código (Oleada 0, serie 41; plan sin contenido del 2026-10-16) | **`PROMPT_SINCRONIZACION_DOCS.md`** y `PLAN_ULTRACODE.md` |
| Verificar una afirmación, cerrar una tarea, elegir modelo y ahorrar tokens | **`PROTOCOLO_VERIFICACION.md`** |
| Trabajar en paralelo: qué ficheros escribe cada sesión, ficheros compartidos, migraciones, i18n por rol | **`SESIONES.md`** |
| Decisiones irreversibles (ADR) | `DECISIONS.md` |
| Plan maestro de la beta: las decisiones D-xx del dueño y su estado | `PLAN_MAESTRO.md` |
| Informe de estado generado (`scripts/estado.py`) | `ESTADO_AUTOMATICO.md` |
| Por qué se pausó el 2026-09-30, el scorecard (§2) y las trampas del entorno (§7). **Pausa levantada el 2026-10-01** (ADR-56) | `CIERRE_2026-09-30.md` |

**Producto y mercado**

| Quieres… | Lee |
|---|---|
| Qué construye Whetzy y qué falta (tracks, certificaciones, fuentes legales, coste) | **`CATALOGO_MAESTRO.md`** (§2.1 fuentes; ADR-11) |
| Cómo se escribe el contenido nuevo (método desde la fuente, piloto, orden y organización) | **`PLAN_CONTENIDO.md`** (ADR-59) |
| Lanzamiento piloto: invitación ES/EN, qué pedir, preguntas del día 4 | **`LANZAMIENTO_PILOTO.md`** |
| Competencia con precios y catálogos verificados (URL y fecha) | **`COMPETENCIA.md`** |
| Posición frente a la competencia con pesos fijos | `competitive-teardown.md` |
| Segmentos de usuario, personas y flujos | **`SEGMENTOS.md`** |
| Plan para superar a Brilliant y Kodree donde hoy ganan (serie 40) | **`PLAN_EXPERIENCIA.md`** |
| Marketplace de instructores (80/20, calidad, moderación) | **`MARKETPLACE.md`** |
| Economía cerrada: créditos, referidos, sin token (ADR-33) | **`ECONOMIA.md`** |
| Distribución ES + EN (canales, cadencia, KPIs) | **`DISTRIBUCION.md`** y `distribucion-assets/` |
| Análisis de negocio de la sesión bf — **no normativo** | `analisis-estrategico/` |

**Técnico y operación**

| Quieres… | Lee |
|---|---|
| Entender el sistema | `ARCHITECTURE.md`, `API.md` |
| Cada pantalla, ruta y `Screen` del frontend, y dónde se especifica (`check_docs.py` [14]) | `MAPA_PRODUCTO.md` |
| Experimentos y calibraciones del motor (BKT/DKT, IRT, beta-binomial, RAG) | `ml/` |
| Simulacro de restauración de la base de datos (lo escribe `scripts/db_restore_test.sh`) | `restore_log.md` |
| Desplegar (Cloudflare y Railway, automáticos desde `master`), migrar, backup, incidentes | `RUNBOOK.md`, `RELEASE.md` |
| Qué servicios externos toca una sesión y qué hace sin preguntar | **`CONECTORES.md`** |
| Capacidad, Cloudflare, cadena de suministro, A/B, diseño | `capacity.md`, `cloudflare-config.md`, `supply-chain.md`, `ab-framework.md`, `design/` |

**Legal y tiendas**

| Quieres… | Lee |
|---|---|
| Textos legales: lo publicado manda (claves i18n `legal.*`; ADR-55), qué hay en `legal/` y procesadores verificados | **`legal/README.md`** |
| Tiendas (ficha, privacidad, checklist de Apple 4.8 / 3.1.1) | `STORE_LISTING.md` (resumen) y `store/` (detalle) |
| Respuestas de soporte ES/EN | `support/` |

**Historia e inventario**

| Quieres… | Lee |
|---|---|
| Historia narrativa por sesión (no se reescribe; no hace falta leerla) | `STATUS.md`, `CHANGELOG.md` |
| Cada `.md` del repo con su clase y qué se hizo con él | **`INVENTARIO_DOCS.md`** |

Todo lo demás está en `archive/` y **no manda**: si algo de `archive/` contradice a un
documento vivo, gana el vivo. Un plan que no sea una fila de `AUTONOMOUS_STATE.md` no es un plan.

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
python scripts/catalog_coverage.py            # lo que falta para el plan ADR-54 (32 × 10 por track, práctica y simulacro de certificación)
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
**Por eso `master` solo lo fusiona el dueño a mano (ADR-45)**: la sesión trabaja en rama + PR.
