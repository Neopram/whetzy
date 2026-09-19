# Whetzy — instrucciones del proyecto

Este proyecto se opera de forma autónoma. **Si arrancas sin instrucciones
específicas del usuario, lee `docs/ORCHESTRATOR.md` y ejecútalo.** No preguntes
qué hacer; el ledger lo sabe.

- Fuente de verdad del progreso: `docs/AUTONOMOUS_STATE.md` — **no lo leas entero**
  (~29.500 tokens). `python scripts/ledger.py next` responde «qué toca ahora» en ~114;
  `show <ID>`, `series <N>`, `blocked`, `inv`, `stats`. Parsea el ledger, no lo duplica:
  la fuente de verdad sigue siendo el markdown (ADR-40)
- Alcance del producto (tracks, certificaciones, fuentes, volúmenes, puerta de calidad): `docs/CATALOGO_MAESTRO.md`
- Estado narrativo e histórico: `docs/STATUS.md` (registro por sesión; no se reescribe hacia atrás)
- Prompt operativo: `docs/ORCHESTRATOR.md`
- Posición competitiva con pesos fijos: `docs/competitive-teardown.md` (última: §11)
- Decisiones irreversibles: `docs/DECISIONS.md` (ADR-11 fuentes, ADR-12 herramientas, ADR-13 social login, ADR-40 memoria en el repo)
- Auditoría externa más reciente (producción medida en vivo, CI, coste de contexto): `docs/AUDITORIA_EXTERNA_2026-09-19.md`
- Guardia docs-vs-código: `python scripts/check_docs.py` (debe pasar antes de cada commit que toque contenido o docs)
- Protocolo de verificación (cada `DONE`, cada doc, modelos y tokens): `docs/PROTOCOLO_VERIFICACION.md`
- Documentos vivos: los del índice `docs/README.md`; `docs/archive/` no manda

## Invariantes

- Backend prod: `https://api-production-9751.up.railway.app` — **deploy AUTOMÁTICO desde `master`** (verificado 2026-09-16, ledger H.16): `git push origin master` despliega backend, migraciones y `content_loader`. Antes de cada push: `pytest tests/content` y `check_question_bank.py` verdes
- Frontend prod: `https://whetzy.com` — **deploy MANUAL** con `npx wrangler pages deploy dist --project-name whetzy --branch main` desde `frontend/` (sin `--branch main` va a Preview). `whetzy.com/health` devuelve el SPA; el health real es el del backend
- Fuentes de contenido: **solo gratuitas y legales** (ADR-11) — reutilizar MIT/Apache/BSD/CC BY/CC0/PSF/dominio público; CC BY-SA espera H.LIC; CC BY-NC y propietario se cita, nunca se copia. Biblioteca: `docs/CATALOGO_MAESTRO.md` §2.1
- Social login: si existe cualquier OAuth, **Sign in with Apple es obligatorio** antes de enviar a App Store (4.8, ADR-13)
- DB local: Docker `:5433`, `neurium` / `neurium_dev` / db `neurium`
- Alembic: nunca `create_all`. Toda migración por `alembic revision`. HEAD actual: `b1c2d3e4f5a6` (28 migraciones)
- LLM: `qwen/qwen3.8-27b` en Groq
- OpenAPI en `/api/v1/openapi.json`; `POST /quiz/start` devuelve el id en `.question.id`

## Modelos

Hilo principal: el que fije `settings.json` (Sonnet 4.6). **Sesiones autónomas: sin
Opus ni Fable** (ADR-14, propuesta del dueño 2026-09-18). Subagentes: **Haiku por
defecto** — inventarios, lecturas masivas, diffs doc↔código, verificación adversaria y
**autoría de contenido por fichero** (siempre con la puerta de calidad de
`CATALOGO_MAESTRO.md` §7); Sonnet solo cuando la tarea escribe en la lista de ficheros de
riesgo de `docs/PROTOCOLO_VERIFICACION.md` §2. Dieta de contexto: el ledger se lee por
secciones, nunca entero; `STATUS.md` y `archive/` no se leen. Bloques de contenido
grandes: `Workflow` paralelo, un bloque = un commit verde. Cada `DONE` pasa por el
verificador adversario (protocolo §7) antes de escribirse.

## Estilo

Tests con el código, no después. Escribe como el código que te rodea. Evidencia
ejecutable o no pasó. Documentación en español; contenido y UI en ES y EN nativos.
El schema de `tracks.json` es `name_es/name_en/order/color/icon` (nunca `title_*`):
el loader hace `data["name_es"]` y revienta con otra forma.

