# Whetzy — instrucciones del proyecto

Este proyecto se opera de forma autónoma. **Si arrancas sin instrucciones
específicas del usuario, lee `docs/ORCHESTRATOR.md` y ejecútalo.** No preguntes
qué hacer; el ledger lo sabe.

- Fuente de verdad del progreso: `docs/AUTONOMOUS_STATE.md`
- Alcance del producto (tracks, certificaciones, fuentes, volúmenes, puerta de calidad): `docs/CATALOGO_MAESTRO.md`
- Estado narrativo e histórico: `docs/STATUS.md`
- Prompt operativo: `docs/ORCHESTRATOR.md`
- Guardia docs-vs-código: `python scripts/check_docs.py` (debe pasar antes de cada commit que toque contenido o docs)

## Invariantes

- Backend prod: `https://api-production-9751.up.railway.app` — **deploy AUTOMÁTICO desde `master`** (verificado 2026-09-16, ledger H.16): `git push origin master` despliega backend, migraciones y `content_loader`. Antes de cada push: `pytest tests/content` y `check_question_bank.py` verdes
- Frontend prod: `https://whetzy.com` — `whetzy.com/health` devuelve el SPA; el health real es el del backend
- DB local: Docker `:5433`, `neurium` / `neurium_dev` / db `neurium`
- Alembic: nunca `create_all`. Toda migración por `alembic revision`. HEAD actual: `s9t0u1v2w3x4` (19 migraciones)
- LLM: `qwen/qwen3.8-27b` en Groq
- OpenAPI en `/api/v1/openapi.json`; `POST /quiz/start` devuelve el id en `.question.id`

## Modelos

Hilo principal: el que fije la app o `settings.json` (Sonnet 4.6 por defecto; Fable 5.1
si el dueño lo elige). Subagentes: Haiku para inventarios, lecturas masivas y **autoría
de contenido por fichero** (siempre con la puerta de calidad de `CATALOGO_MAESTRO.md` §7),
Sonnet para implementar y verificar, Opus solo arquitectura irreversible y máximo 2 por
sesión. Bloques de contenido grandes: `Workflow` paralelo, un bloque = un commit verde.

## Estilo

Tests con el código, no después. Escribe como el código que te rodea. Evidencia
ejecutable o no pasó. Documentación en español; contenido y UI en ES y EN nativos.
El schema de `tracks.json` es `name_es/name_en/order/color/icon` (nunca `title_*`):
el loader hace `data["name_es"]` y revienta con otra forma.
