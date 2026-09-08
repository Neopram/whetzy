# Whetzy — Ledger autónomo de ejecución

> **Este archivo es la fuente de verdad del progreso.** El orquestador lo lee al
> arrancar y lo escribe al cerrar. No lo edites a mano salvo para cambiar prioridades
> o desbloquear un ítem de `HUMAN-BLOCKED`.
>
> Formato de estado: `TODO` · `DOING` · `DONE` · `BLOCKED` · `HUMAN-BLOCKED`
>
> Última actualización: 2026-09-08 (sesión s) — inicialización del ledger

---

## 0. Invariantes del sistema (no romper nunca)

| Invariante | Valor |
|---|---|
| Backend prod | `https://api-production-9751.up.railway.app` |
| Frontend prod | `https://whetzy.com` / `https://whetzy.pages.dev` |
| Repo | `github.com/Neopram/whetzy` branch `master` |
| Alembic HEAD | cadena `<base> → a1b2c3d4e5f6 → b2c3d4e5f6a7` (+ las que añadas) |
| DB local | Docker :5433, user `neurium`, pass `neurium_dev`, db `neurium` |
| Modelo LLM | `qwen/qwen3.8-27b` en Groq (llama-3.3-70b NO disponible) |
| Railway deploy | **MANUAL** — sin webhook GitHub. CLI token viejo expirado |
| Contenido | 1253 preguntas / 7 tracks / 207 skills / 70 términos glosario |

### Gotchas verificados (no redescubrir)
- `POST /quiz/start` → `question_id` está en `.question.id`, **no** en `.id`
- `POST /auth/register` → devuelve token directo; `POST /auth/login` requiere **form-urlencoded**
- `POST /duels/{id}/answer` → requiere `selected_index` + `response_time_ms`
- `POST /duels/challenge` → devuelve `questions[]`, **no** `question_ids[]`
- `GET /api/v1/glossary/track01` → track_id es string `"track01"`, no int
- `whetzy.com/health` → devuelve HTML del SPA. Health real: `<backend>/health`
- OpenAPI está en `/api/v1/openapi.json`, **no** en `/openapi.json`
- Archivos escritos con Write tool en sesiones **previas** pueden ser invisibles a
  `os.listdir()` en subprocess Python. Fix: reescribirlos en la sesión actual
- `content_loader` solo corre desde `start.sh` en prod. En dev, ejecutarlo a mano

---

## 1. Estado por fase

| Fase | Área | % | Estado |
|---|---|---|---|
| 0 | Rebrand + Auth + Deploy | 100% | ✅ CERRADA |
| 1 | Contenido bilingüe + glosario + currículo | 100% | ✅ CERRADA |
| 2 | Tutor AI (Groq) + RAG | 98% | Pyodide sin browser-test |
| 3 | Gamificación + duelos + offline + Lottie | 92% | Duel E2E prod ✅; Pyodide pendiente |
| 4 | DKT + churn + MLOps | 15% | DKT MVP inferencia ✅; sin training/eval/churn |
| 5 | Pipeline multi-agente + analytics | 3% | No construido |
| 6 | Observabilidad + límites de servicio | 5% | Monolito, logging básico |
| 7 | Commerce + i18n + nativo + IaC + seguridad | 30% | Docker/CI reales; sin Stripe/nativo/K8s |
| 8 | Garantía E2E + informe competitivo | 20% | Sin Playwright, sin load test |
| 9 | Store readiness + excelencia de diseño | 0% | No iniciado |
| Q | Piso de calidad (transversal) | 12% | 3 test files de ~50 necesarios |

---

## 2. Backlog ejecutable

> Orden de ejecución = por `PRI` ascendente, luego por ID. `PRI 0` es lo que
> desbloquea todo lo demás.

### Q — Piso de calidad (transversal, PRI 0-1)

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| Q.1 | 0 | Infra de tests backend: `pytest.ini`/`conftest.py` con DB efímera, fixtures de user/token/content | TODO | `pytest backend/tests` corre en <60s contra SQLite en memoria, 0 errores de setup |
| Q.2 | 0 | Tests unitarios del engine: FSRS, Elo, BKT, bandit | TODO | ≥90% cobertura en `services/engine/`, casos borde incluidos |
| Q.3 | 1 | Tests de integración API: auth, quiz, progress, glossary, duels, placement, tutor | TODO | Cada endpoint con happy path + 401 + 422 + caso borde. ≥80% cobertura en `api/v1/` |
| Q.4 | 1 | Tests de gamificación: XP, ligas, badges, misiones, rachas | TODO | ≥85% cobertura en `services/gamification/` |
| Q.5 | 1 | Inventario y eliminación de código muerto | TODO | `vulture`/`ruff --select F401,F841` limpio. Cada borrado justificado con grep de referencias |
| Q.6 | 1 | Consolidación de docs: 10 archivos → set coherente | TODO | `docs/` con: README, ARCHITECTURE, API, RUNBOOK, STATUS, DECISIONS. Prompts históricos a `docs/archive/` |
| Q.7 | 2 | Type strictness: mypy strict backend, tsc strict frontend | TODO | `mypy app --strict` 0 errores; `tsc --noEmit --strict` 0 errores |
| Q.8 | 2 | Lint zero-warnings: ruff + eslint | TODO | `ruff check` y `eslint` sin warnings. Reglas en CI |
| Q.9 | 2 | Tests frontend: vitest + testing-library para hooks y componentes críticos | TODO | ≥70% en `src/hooks/` y `src/services/`. QuizScreen, DuelScreen con render tests |
| Q.10 | 3 | CI real: lint + mypy + pytest + tsc + vitest + build (branch ya corregido a `master` en sesión s) | TODO | GH Actions verde en push con todos los pasos; sin `\|\| true` |

### 2 — Cierre Fase 2

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 2.1 | 2 | Pyodide E2E determinista: endpoint dev que fuerza pregunta `exec` | TODO | Test Playwright: recibe `fill_blank_exec`, ejecuta, output correcto, 0 errores consola |
| 2.2 | 3 | Sandbox hardening Pyodide: timeout, memoria, imports bloqueados | TODO | Test: `while True: pass` termina en 5s; `import os` bloqueado |
| 2.3 | 3 | `exec_correct` server-side (hoy viene del cliente = explotable) | TODO | Servidor valida output; cliente no puede falsear corrección |

### 3 — Cierre Fase 3

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 3.1 | 2 | Duel E2E en browser (2 usuarios, Playwright) | TODO | Reto → ambos responden → resultado con ganador, verificado en UI |
| 3.2 | 3 | Offline sync E2E: responder offline → volver online → sync verificado | TODO | Playwright con `context.setOffline(true)`; respuesta persiste y sincroniza |
| 3.3 | 3 | Notificaciones de duelo (push web) | TODO | Web Push registrado; reto genera notificación |

### 4 — DKT + Churn + MLOps

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 4.1 | 2 | Pipeline de entrenamiento DKT: dataset desde `responses`, split temporal | TODO | `python -m app.ml.train_dkt` produce checkpoint versionado |
| 4.2 | 2 | Harness de evaluación: AUC/ACC de DKT vs BKT baseline | TODO | Reporte con AUC de ambos; DKT ≥ BKT o se documenta por qué no |
| 4.3 | 3 | Registro de modelos: checkpoints versionados, carga en startup, rollback | TODO | `models/dkt/v{N}/` + metadata; API reporta versión activa |
| 4.4 | 3 | Caché de inferencia (no correr LSTM por request) | TODO | p99 de `/progress/skills` < 200ms con DKT activo |
| 4.5 | 3 | Predictor de churn: features + modelo + endpoint | TODO | `GET /progress/risk` devuelve score + factores; AUC > 0.7 en holdout |
| 4.6 | 4 | Harness A/B: selección BKT vs DKT por cohorte | TODO | Flag por usuario; métricas comparables por cohorte |

### 5 — Pipeline multi-agente + analytics

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 5.1 | 3 | Agente autor de contenido: genera Q desde fuente con cita | TODO | Genera 10 Q válidas de un doc fuente; schema válido, source poblado |
| 5.2 | 3 | Agente QA de contenido: valida distractores, dificultad, cita | TODO | Detecta ≥90% de Q sembradas con defectos conocidos |
| 5.3 | 4 | Detección de duplicados por embeddings | TODO | Detecta paráfrasis en el banco actual; reporte de candidatos |
| 5.4 | 3 | Esquema de eventos de analytics + ingesta | TODO | Eventos tipados; funnel registro→primer quiz→D1→D7 consultable |
| 5.5 | 4 | Dashboard de analytics (admin) | TODO | Retención, engagement, dominio por skill, embudo |

### 6 — Observabilidad + límites de servicio

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 6.1 | 1 | Logging estructurado JSON con `request_id` correlacionado | TODO | Cada log lleva request_id, user_id, path, latencia |
| 6.2 | 2 | OpenTelemetry: trazas HTTP + DB | TODO | Traza de una request de quiz muestra spans de DB |
| 6.3 | 2 | Métricas Prometheus + `/metrics` | TODO | RED metrics (rate/errors/duration) por endpoint |
| 6.4 | 2 | Error tracking (Sentry-compatible) | TODO | Excepción no capturada llega con stack + contexto de usuario |
| 6.5 | 1 | Liveness vs readiness separados | TODO | `/health/live` y `/health/ready`; ready verifica DB |
| 6.6 | 1 | Rate limiting por IP y por usuario | TODO | 429 con `Retry-After`; login y tutor con límites más estrictos |
| 6.7 | 4 | Límites de servicio limpios (interfaces, no microservicios prematuros) | TODO | `content`, `engine`, `gamification` con interfaces explícitas y sin imports cruzados |

### 7 — Commerce + i18n + nativo + IaC + seguridad

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 7.1 | 2 | Auditoría de seguridad ASVS L2 + fixes | TODO | Checklist ASVS L2 completo; todo hallazgo alto/crítico corregido |
| 7.2 | 2 | Stripe: checkout + webhook + estado de suscripción | TODO | Test-mode E2E: checkout → webhook → entitlement activo |
| 7.3 | 2 | Entitlements: gating free/plus/pro | TODO | Feature gates server-side; cliente no puede saltárselos |
| 7.4 | 3 | i18next completo ES/EN | TODO | 0 strings hardcodeados; cambio de idioma en caliente |
| 7.5 | 3 | Shell nativo Capacitor (iOS + Android) | TODO | Builds locales corren; deep links; safe areas |
| 7.6 | 4 | RevenueCat IAP nativo | TODO | Sandbox purchase E2E en ambas plataformas |
| 7.7 | 4 | IaC: Terraform para Railway + Cloudflare | TODO | `terraform plan` limpio; infra reproducible |
| 7.8 | 2 | Runbook de backup/restore de DB | TODO | Restore probado en DB efímera desde backup real |

### 8 — Garantía E2E + competitivo

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 8.1 | 1 | Suite Playwright: auth, quiz, duelo, offline, pago | TODO | Verde en CI headless; screenshots en fallo |
| 8.2 | 3 | Load test (k6): 100 usuarios concurrentes | TODO | p95 < 500ms, 0 errores 5xx |
| 8.3 | 3 | Presupuesto de performance | TODO | LCP < 2.5s, TTI < 3.5s, bundle < 300KB gzip |
| 8.4 | 4 | Teardown competitivo vs Duolingo/Brilliant/DataCamp | TODO | Informe con gaps concretos y acciones |

### 9 — Store readiness + excelencia de diseño

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 9.1 | 2 | Revisión del sistema de diseño: tokens, motion, jerarquía | TODO | Tokens coherentes; sin valores mágicos; motion con `prefers-reduced-motion` |
| 9.2 | 2 | Accesibilidad WCAG 2.2 AA | TODO | axe-core 0 violaciones; navegación por teclado completa; contraste AA |
| 9.3 | 3 | Assets de store: iconos, screenshots, video preview | TODO | Todos los tamaños iOS/Android generados desde fuente vectorial |
| 9.4 | 2 | Legal: privacidad, ToS, borrado de datos (GDPR/CCPA) | TODO | Páginas publicadas y enlazadas; flujo de borrado funcional |
| 9.5 | 3 | Checklist App Store Review Guidelines | TODO | Cada guideline aplicable evaluada con evidencia |
| 9.6 | 3 | Play Store: Data Safety + target API level | TODO | Formulario completo y consistente con el código real |
| 9.7 | 3 | Audit de accesibilidad nativa (VoiceOver/TalkBack) | TODO | Flujos principales navegables con lector de pantalla |
| 9.8 | 4 | Sitio de marketing + pricing | TODO | Landing con propuesta de valor, pricing, CTA a checkout |

### Dependencias

No arrancar la tarea de la izquierda sin las de la derecha en `DONE`:

| Tarea | Requiere |
|---|---|
| Q.2, Q.3, Q.4, Q.9 | Q.1 |
| Q.7, Q.8 | Q.5 |
| Q.10 | Q.1, Q.7, Q.8 |
| 2.1, 3.1, 3.2 | 8.1 |
| 4.2, 4.3, 4.4 | 4.1 |
| 4.6 | 4.2, 4.3 |
| 5.2 | 5.1 |
| 5.5 | 5.4 |
| 6.2, 6.3, 6.4 | 6.1 |
| 7.3 | 7.2 |
| 7.6 | 7.5 |
| 9.3, 9.5, 9.6, 9.7 | 7.5 |
| 9.8 | 7.2 |

### Grupos paralelos

Archivos disjuntos garantizados. Pueden correr como workers simultáneos
(máx. 3). Si una tarea no aparece aquí, va en serie.

| Grupo | Tareas | Disjunción |
|---|---|---|
| G1 | Q.2 ‖ Q.4 ‖ Q.5 | `tests/unit/engine/` ‖ `tests/unit/gamification/` ‖ solo lectura + reporte |
| G2 | Q.3a (auth, quiz) ‖ Q.3b (progress, glossary, placement) ‖ Q.3c (duels, tutor) | un archivo de test por endpoint |
| G3 | 6.1 ‖ 6.5 ‖ 6.6 | `core/logging.py` ‖ `api/health.py` ‖ `core/ratelimit.py` |
| G4 | 4.1 ‖ 5.4 ‖ 7.1 | `app/ml/` ‖ `app/analytics/` ‖ informe + fixes puntuales |
| G5 | 9.1 ‖ 9.4 ‖ 7.4 | `design-tokens.css` + componentes ‖ `legal/` + páginas ‖ `i18n/` |

---

## 3. Cola HUMAN-BLOCKED

> El orquestador **prepara todo** y deja el ítem aquí. No intenta ejecutar la acción final.

| ID | Bloqueo | Qué preparó el agente | Qué debe hacer el humano |
|---|---|---|---|
| H.1 | Railway deploy manual | Código en `master`, `start.sh` con auto-stamp | railway.app → servicio → Deploy del último commit |
| H.2 | Apple Developer Program | — | Cuenta ($99/año) + certificados |
| H.3 | Google Play Console | — | Cuenta ($25 único) |
| H.4 | Stripe cuenta live | Integración en test-mode | Activar cuenta, claves live |
| H.5 | Submisión a stores | Assets + checklists | Subir builds y responder review |
| H.6 | Cadena de sesiones | Task recurrente `whetzy-orch-*` cada 6 h; modelo y permisos en `~/.claude/settings.json`; se auto-borra al agotar el backlog | Nada, salvo tener la app Claude abierta. Pausar: deshabilitar el task en "Scheduled". Quitar la dependencia de la app → H.7 |
| H.7 | Rutina remota — única forma de no depender de la app abierta | `RemoteTrigger` responde 200. Schema sondeado: `session_request.worker` (obligatorio) o `job_config` forma "ccr". El preflight del servidor falla sin repo conectado y entorno | **Una vez:** en claude.ai conectar `Neopram/whetzy` y crear un entorno. La siguiente sesión detecta ambos, cierra el schema con 1-2 creates, migra la cadena y borra el task local |

---

## 4. Scorecard (histórico)

> Una fila por sesión. El orquestador la añade al cerrar, con números medidos, no estimados.

| Sesión | Fecha | Tests pasando | Cobertura back | Cobertura front | Ruff | mypy | tsc | Tareas DONE | Fases ≥95% |
|---|---|---|---|---|---|---|---|---|---|
| s | 2026-09-08 | 3 archivos, sin medir | — | — | — | — | 0 err | — | 0,1 |

---

## 5. Bitácora de decisiones

> Decisiones de arquitectura irreversibles o costosas de revertir. Formato ADR corto.

| # | Fecha | Decisión | Razón | Alternativas descartadas |
|---|---|---|---|---|
| 1 | 2026-09-07 | Monolito FastAPI, no microservicios | Equipo de 1, tráfico bajo, complejidad no justificada | K8s + servicios separados |
| 2 | 2026-09-07 | Groq + qwen3.8-27b | Gratis, latencia baja | OpenAI (coste), Llama-3.3-70b (no disponible) |
| 3 | 2026-09-08 | Alembic con auto-stamp en `start.sh` | DB de prod preexistente sin `alembic_version` | Recrear DB (pierde usuarios) |
| 4 | 2026-09-08 | DKT con torch opcional + fallback EWA | Railway free tier puede no soportar torch | torch obligatorio (riesgo OOM) |
| 5 | 2026-09-08 | Orquestación por ledger + auto-programación de sesiones (scheduled task local, one-shot +6h) | Un prompt monolítico degrada la atención; el estado debe vivir fuera del contexto. One-shot en vez de cron: cada sesión decide si hay trabajo antes de programar la siguiente, y la cadena se corta sola sin presupuesto | Cron ciego (quema presupuesto sin mirar el ledger); un solo prompt gigante |
| 6 | 2026-09-08 | Workers paralelos sin worktree por defecto, sobre grupos de archivos disjuntos | Evita el coste de merge; la disjunción la garantiza el ledger. Worktree solo para refactors amplios | Worktree siempre (merge en cada tarea) |
| 7 | 2026-09-08 | Continuidad por task recurrente (cron 6 h) que el propio orquestador convierte en su pre-flight y borra al terminar; modelo y permisos en settings de usuario | Una cadena one-shot muere si un corte por límite llega antes de programar la siguiente. El cron reintenta solo: sin trabajo sale en segundos, sin presupuesto no arranca y no gasta. Settings de usuario aplican en cualquier cwd, que el task no controla | Cadena one-shot (frágil); bypass a nivel proyecto (no aplica si el task arranca fuera del cwd) |

---

## 6. Cadena de sesiones

> Una fila por sesión programada. La sesión que la crea la anota; la que la
> consume la marca.

| taskId | Programada para | Creada por | Estado |
|---|---|---|---|
| whetzy-orch-20260911-0730 | 2026-09-11 07:30 one-shot → cron `23 */6 * * *` en su primer pre-flight | sesión s | ARMADO |
