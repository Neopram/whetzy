# Whetzy — instrucciones del proyecto

Este proyecto se opera de forma autónoma. **Si arrancas sin instrucciones
específicas del usuario, lee `docs/ORCHESTRATOR.md` y ejecútalo.** No preguntes
qué hacer; el ledger lo sabe.

- Fuente de verdad del progreso: `docs/AUTONOMOUS_STATE.md`
- Estado narrativo e histórico: `docs/STATUS.md`
- Prompt operativo: `docs/ORCHESTRATOR.md`

## Invariantes

- Backend prod: `https://api-production-9751.up.railway.app` — deploy **manual**, sin webhook GitHub
- Frontend prod: `https://whetzy.com` — `whetzy.com/health` devuelve el SPA; el health real es el del backend
- DB local: Docker `:5433`, `neurium` / `neurium_dev` / db `neurium`
- Alembic: nunca `create_all`. Toda migración por `alembic revision`. HEAD actual: `b2c3d4e5f6a7`
- LLM: `qwen/qwen3.8-27b` en Groq
- OpenAPI en `/api/v1/openapi.json`; `POST /quiz/start` devuelve el id en `.question.id`

## Modelos

Hilo principal: Sonnet 4.6 (lo fija la app). Subagentes: Haiku para inventarios y
lecturas masivas, Sonnet para implementar, Opus solo arquitectura irreversible y
máximo 2 por sesión.

## Estilo

Tests con el código, no después. Escribe como el código que te rodea. Evidencia
ejecutable o no pasó.
