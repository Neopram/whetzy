# Plan ultracode — sincronizar toda la documentación y cerrar lo roto (sin contenido)

> **Normativo-vivo.** Petición del dueño del 2026-10-16. Plan escrito sobre `master` `e85900b`; esta
> copia entra en el repo sobre `fa1af50` (tras #217-#221). §0 dice qué ha cambiado desde `e85900b`. Las
> secciones §5-§10 son las del plan del dueño, sin reescribir. Los números ADR-61…64 y H.51…H.57 son
> provisionales: la sesión que ejecute los confirma con
> `grep -n '^## ADR-' docs/DECISIONS.md | tail -1` y `grep -n '^| H\.' docs/AUTONOMOUS_STATE.md | tail -1`.
> Prompt de la Oleada 0: `docs/archive/PROMPT_SINCRONIZACION_DOCS.md` (ejecutado el 2026-10-16). Serie 41 y 42 del ledger.

## 0. Diferencias con `e85900b` (comprobadas sobre `fa1af50`)

Comprobado el 2026-10-16 con un `Workflow` de solo lectura: 9 lectores, cada cambio de veredicto
refutado por un segundo agente, y los marcados ★ repetidos a mano. Se revisaron 54 afirmaciones del
plan; 42 siguen siendo ciertas en la línea citada. Las demás:

**Ya hecho en `master` desde `e85900b`. La sesión que ejecute no lo rehace: lo verifica y cierra la fila.**

| Fila | Qué decía el plan | Hoy en `fa1af50` |
|---|---|---|
| 42.1 Oleada 1 | `engine/placement.py:160` Newton con 2.ª derivada mal → θ=±4 | ★ EAP con prior N(0,1) (#219, `b984233`); `grep -c d2l` da 0; guarda `backend/tests/unit/test_placement_theta.py`. Falta lo que #219 no hizo: el log de `_rebuild_state` (`services/placement.py:106-107` sigue con `continue` mudo), la simulación de la parada por SE y el gancho `prior_mean` de la Oleada 5 |
| 42.2 Oleada 2a | `playwright.config.ts:33-41` sin el origen 5199 | ★ `playwright.config.ts:50` con `BACKEND_CORS_ORIGINS: JSON.stringify([...5199, ...5173])` (#220, `2695ed0`). **Sigue pendiente**: el paso e2e en `ci_local.sh` (`grep -i playwright scripts/ci_local.sh` da 0) y la guarda de contrato puerto ↔ CORS. Nota: el formato por comas (`config.py:101-106`) rompía el arranque desde el `env` de Playwright; por eso va en JSON |
| 42.3 Oleada 2b | 13 specs en rojo, `helpers.ts:109-139` con localizadores ambiguos | #217 (`e7cda41`) y #220: E2E 54/56 en local; `answerCurrentQuestion` en `helpers.ts:114-127` por rol y nombre. Queda revisar los 2 saltados y el diagnóstico de `/auth/me` colgado (`tryRefresh` sin promesa compartida sigue en `api.ts:131-143`) |
| 42.10 Oleada 6 | `useAppStore.ts:222` sin `pushState` | ★ `frontend/src/lib/screenHistory.ts:84` hace `pushState` y `App.tsx` llama a `useScreenHistory` (#218, `513a800`). Cambio de diseño respecto al plan: cada pantalla principal tiene **su URL** (`SCREEN_PATHS`), no «/». Queda el atrás de Android (cola humana) |

**La afirmación sigue en pie, pero la cita estaba mal.**

| Cita del plan | Correcta |
|---|---|
| `backend/app/services/bkt.py:22` | ★ `backend/app/services/engine/bkt.py:22` (`p_l0: float = 0.1`) |
| `quiz.py:144-183`, `:420`, `:472-476`, `:630-645` (endpoint) | ★ `backend/app/services/quiz.py` (`apply_answer_to_skill_state` en `:136`); `endpoints/quiz.py` no contiene esos símbolos |
| `engine/placement.py:91` (Thompson) | `engine/placement.py:106` y `:117` (`gammavariate`) |
| `engine/placement.py:203,226` (D-17/D-18) | `services/placement.py:203,226`, y solo D-18; D-17 está en `schemas/exam.py:112` |
| `offlineQueue.ts:44` `declaredUnknown` en `false` | ★ `hooks/useOfflineSync.ts:44`: pasa un `false` literal; `offlineQueue.ts` no guarda ese campo |
| `config.py:100-105` | `config.py:101-106` |
| `catalog.ts:12-13` «35 rutas» | ★ `catalog.ts:9` `CATALOG_TRACKS = 35`; `catalog_coverage.py`: 45 del plan, 24 construidos, 1 en la forma ADR-54 |
| `App.tsx:189-191`, `:356-360` | `App.tsx:190-192`, `:355-361` |
| `check_docs.py:420` ([11]) | la cabecera de [11] está en `:408`; `:420` es una línea dentro de esa guarda |

**Línea base de esta copia**: el ledger pasa a medir 61.136 B, con 304 B de margen sobre 61.440, tras
añadir la serie 41 mínima. 41.1 va primero.

**Cambios hechos al copiar el plan del dueño** (no hay más):
- Se quitaron números de línea que este mismo PR desplaza: CLAUDE.md:75/77 y AUTONOMOUS_STATE :513, :515 y :563.
- En R11, «§2» pasa a «el plan del dueño §2», porque §2 no se copia aquí.

## 5. Oleadas de código (las ejecutan sesiones posteriores con `Workflow`)

Reglas comunes: rama `claude/ultracode-<n>-<tema>` y PR desde el primer commit; test primero
(commit 1: tests nuevos con su salida en ROJO sobre master pegada en el PR; commit 2: corrección y
verde); cada guarda mutada hasta verla en rojo; cierre con `bash scripts/ci_local.sh` entero y la
puerta `.githooks/pre-push`; docs vivos que el cambio invalida se actualizan en el mismo PR (y
`docs/API.md` si hay ruta nueva, check [5c]); migraciones con `downgrade` probado y las tres líneas
de HEAD (CLAUDE.md:62, ledger, RUNBOOK); cada DONE por el verificador §7 (Haiku Explore); workers
de escritura y revisión Sonnet; `git diff --name-only origin/master | grep '^content/'` vacío.
Orden: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9. Paralelizables en worktrees desde master: 1, 2a, 6, 7, 8.
Encadenadas: 3 → 4 → 5 (comparten `quiz.py:144-183` y `UserSkillState`). Playwright no se
paraleliza (puertos fijos 8000 y 5199, `playwright.config.ts`).

| Oleada | Fila | Tamaño | Objetivo | Ficheros clave | Tests nuevos (rojos hoy) | Verde (bucle corto) | Workflow |
|---|---|---|---|---|---|---|---|
| 1 Estimador de la prueba de nivel | 42.1 | M | EAP en rejilla de 81 puntos en [−4,4] con prior N(μ0,σ0) (`prior_mean`, `prior_sd`, gancho de la Oleada 5); SE = desviación a posteriori; sin derivadas. Alternativa B: MAP con puntuación de Fisher, paso acotado | `engine/placement.py:130-181,201-218`; `services/placement.py:93-109` (`_rebuild_state`; descarta en silencio preguntas fuera del pool: añadir log); `PlacementScreen.tsx:27-41` | `backend/tests/unit/test_placement_estimator.py`: derivada vs diferencia finita; una respuesta ⇒ \|θ\|<1; acierto b=0 + fallo b=1,73 ⇒ 0<θ<1,73; monotonía; invariante al orden; simulación RMSE<0,5 a n=30; parada solo con n≥20 y (n=50 o SE≤0,30). Vitest de frontera para `nivelDeTheta` | `cd backend && python -m pytest tests/unit/test_placement_params.py tests/unit/test_placement_estimator.py tests/unit/test_placement_keeps_mastery.py tests/integration/test_placement.py tests/integration/test_placement_pool.py tests/integration/test_cadena_placement_practica.py tests/test_placement_regla_visible.py tests/unit/test_irt_calibration.py -q`; `cd frontend && npx vitest run src/test/placement.test.tsx`. Añadir el fichero nuevo a `.githooks/pre-push:149-163` | autor de tests → implementador (no edita tests) → simulación/calibración (tabla en `docs/ml/`) → verificador §7; 4 agentes, un solo árbol |
| 2a Puerta E2E | 42.2 | S | Origen 5199 en el `env` del webServer del backend (`playwright.config.ts:33-41`, tras `DEFAULT_RATE_LIMIT`; el validador `config.py:100-105` acepta lista por comas; con `ENVIRONMENT: test` los loopback se conservan); paso `correr "frontend: e2e (Playwright)" … npm run -s test:e2e` en `ci_local.sh` tras `:356` con BD temporal fuera del proyecto como el job `e2e` de `ci.yml:150-171` (Postgres 16); si no hay Postgres local, salto visible `[--]` que NO cuenta como verde | `frontend/playwright.config.ts`, `scripts/ci_local.sh`, `backend/tests/test_e2e_cors_contract.py` (patrón `test_constantes_planes.py`) | guarda de contrato puerto ↔ `BACKEND_CORS_ORIGINS` (mutación: cambiar el puerto) | `cd frontend && npx playwright test`; `bash scripts/ci_local.sh` | implementador + verificador |
| 2b Specs y diagnóstico | 42.3 | M-L | onboarding×2 y mobileNoScroll reescritos al flujo real; helper `answerCurrentQuestion` (`e2e/helpers.ts:109-139`: localizadores únicos, «Confirmar»); gamification con cabecera `Origin` en `page.request`; auth.spec con `context.clearCookies()`; oauth×2 sin `networkidle` y diagnóstico de las 4 peticiones `/auth/me` y `/auth/refresh` colgadas (hipótesis a descartar: `tryRefresh` sin promesa compartida `api.ts:131-143`, efectos solapados en `App.tsx` y `authRedirect.ts`, StrictMode; método: `page.on('request'/'requestfinished'/'requestfailed')` y traza); certifying-exam `test.skip` con causa (paywall en False); pyodide y js_exec: determinar causa (¿red/CDN?) y etiquetar o arreglar | `frontend/e2e/*.spec.ts`, `frontend/e2e/helpers.ts`, `frontend/src/services/api.ts` | los 13 specs | `cd frontend && npx playwright test` sin rojos; saltos uno a uno con causa en el PR | 4 escritores en worktrees (onboarding+mobile; quiz+duel+helper; auth+gamification+oauth; pyodide+js_exec+certifying) + 1 diagnosticador + verificador; ejecuciones con servidores una a una desde el hilo principal |
| 3a Duelos: correcciones | 42.4 | M | 202 ≠ «Perdiste»: mantener el contrato del backend (`test_duels.py:567-580` aserta 202) y en `duels.result` (`api.ts`) devolver `pending` si `res.status === 202`; `DuelScreen.tsx:236-249` muestra «esperando a tu rival»; `DuelAnswerResponse` (`schemas/duel.py:30-34`) devuelve `correct`, índice correcto y explicación; cotas `response_time_ms` 0…300.000 y `selected_index` validado contra las opciones; desempate con tiempo medido en servidor (marca por respuesta dentro del JSON, sin migración); `leagues_opt_out` (`user.py:139`) ⇒ no retar ni ser retado (H.52); copy «en vivo» → asíncrono (`currency.ts:80,88`, i18n `onboarding.f2d` ES/EN) con guarda | `endpoints/duels.py`, `schemas/duel.py`, `DuelScreen.tsx`, `api.ts`, i18n | `test_duels.py`: feedback; 422 por cota; empate por tiempo de servidor aunque el perdedor declare 0; reto a quien salió de ligas; `test_league_participation.py`; `duelScreen.v2.test.tsx` (202 → «esperando») | `cd backend && python -m pytest tests/integration/test_duels.py tests/integration/test_league_participation.py -q`; `cd frontend && npx vitest run src/test/duelScreen.v2.test.tsx src/test/api.wrappers.test.ts && npx playwright test e2e/duel.spec.ts` | autor de tests, backend, frontend (worktrees), verificador |
| 3b Duelos: reanudación y caducidad | 42.5 | M | `/join` admite al retador mientras no haya completado (cambia `test_join_only_opponent_can_join`, `test_duels.py:693`: un tercero sigue en 403/404); «Continuar» en la lista; caducidad perezosa a 7 días (estado `expired`, sin rating), sujeta a H.52; `authz_matrix.json` y `API.md` si hay ruta | `duels.py:262-294`, `DuelScreen.tsx` | reanudación; tercero rechazado; caducado | igual que 3a | 2 escritores + verificador |
| 4 Readiness y dominio | 42.6, 42.7 | L | `compute_domain_mastery` promedia TODAS las skills del dominio (sin estado = 0) y devuelve cobertura (`domain_mastery.py:56-75`, `DOMAIN_READY_THRESHOLD = 0.75` en `:40`); puerta de evidencia en backend (`MIN_EVIDENCE_ANSWERS` en config junto a `MASTERY_THRESHOLD`, `config.py:379`), el API devuelve respuestas y banda y `evidenceBand.ts` consume el campo; una definición de dominio en `engine/domain_thresholds.py` usada por `progress.py:154`, `gamification/service.py:315`, `domain_report.py`; desbloqueo de módulo (0,7, `config.py:380`, `content.py:69`) nombrado como otro concepto; conformar con ADR-60 UX-DEC-01 (`DECISIONS.md:1506-1560`); `exam_pass_predictor.py` (sin importadores en `backend/app`): mover a `backend/app/ml/` o conectar tras bandera (H.53) | `domain_mastery.py`, `certification.py`, `exams.py:204-205,269-303`, `progress.py`, `domain_thresholds.py`, `ReadinessScreen.tsx:72,96`, `evidenceBand.ts` | dominio con skills sin intentar baja el readiness; puerta de 7 en backend; contrato constante frontend ↔ backend | `cd backend && python -m pytest tests/unit/test_domain_mastery.py tests/unit/test_certification_readiness.py tests/unit/test_exam_pass_predictor.py tests/unit/test_domain_thresholds_guard.py tests/integration/test_progress.py -q`; `cd frontend && npx vitest run src/test/readinessScreen.v2.test.tsx src/test/evidenceBand.test.ts` | autor de tests, backend, frontend, verificador |
| 5 Prior y evidencia por fuente | 42.8, 42.9 | L | Bloqueada hasta que el dueño firme ADR-63 (H.51). 42.8: `initial_p_known(onboarding_experience)` como única fuente del punto de partida (`bkt.py:22,131-133`; `quiz.py:123`; `user.py:178`; `placement.py:235`) y `prior_mean` del estimador; siembra de la prueba con encogimiento `(aciertos + k·prior)/(n + k)`, k=4, tope 0,94 (`placement.py:189,223-231`), D-18 intacto; no cambiar la semántica de `economy.py:379,394`. 42.9: `apply_evidence(source, …)` generaliza `apply_answer_to_skill_state` (`quiz.py:144-183`; usada por quiz, duelo `duels.py:334`, test-out `exams.py:395`); contadores por fuente en `UserSkillState` (migración mínima, sin backfill); la puerta de evidencia cuenta solo práctica. Opcional 5c: «onboarding hecho» en servidor (hoy solo localStorage, `App.tsx:189-191`) y botón «omitir» | ver objetivo | `test_evidence_policy.py` (tabla por fuente, mutación: invertir el tope de duelo); prior 0/1/2; placement 1/1 ≪ 0,94; `test_migration_data.py` | `cd backend && python -m pytest tests/unit/test_onboarding_profile.py tests/unit/test_onboarding_c1.py tests/unit/test_evidence_policy.py tests/integration/test_placement.py tests/unit/test_placement_keeps_mastery.py -q` | ADR firmado → autor de tests → backend → migración (agente propio, `downgrade`) → frontend (5c) → verificador; coordinar en #89 |
| 6 Historial de pantallas | 42.10 | M | `setScreen` (`useAppStore.ts:222`) hace `history.pushState({screen}, '', location.pathname)` (URL sigue en «/»; MAPA_PRODUCTO y check [14] intactos); `popstate` restaura sin volver a empujar; arranque con `replaceState`; respetar pantallas inmersivas (`immersiveScreens.ts`) y gestos (`App.tsx:356-360`); no romper #215 (`e2e/back-navigation.spec.ts`). Android: comprobación manual en cola humana; `@capacitor/app` (no está en `package.json`) solo si hace falta, decisión aparte | `useAppStore.ts`, `App.tsx` | `useAppStore.history.test.ts` (push en cambio, pop restaura, sin duplicados; mutación: quitar `pushState`); e2e home → tracks → quiz → atrás → tracks → atrás → home, también a 390 px | `cd frontend && npx vitest run src/test/useAppStore.history.test.ts && npx playwright test e2e/back-navigation.spec.ts` | autor de tests, implementador, verificador |
| 7 Offline sin pérdida | 42.11 | M | `peekAll()` + `remove(id)` tras confirmar cada envío (hoy `dequeueAll` vacía en la misma transacción, `offlineQueue.ts:57-78`); `flush` (`useOfflineSync.ts:28-53`) se detiene ante error transitorio (`ApiError.esTransitorio`, `api.ts:36`) y conserva el resto; 409 por idempotencia (`quiz.py:630-645`, `session.py:85-87`) cuenta como éxito; 4xx definitivo a un almacén de descartes con contador; `declaredUnknown` guardado y enviado (hoy `false`, `:44`); reintento con retroceso además del evento `online`; registrar (no arreglar) que la prueba de nivel no manda `event_id`; al terminar, ORCHESTRATOR.md:92-93 pasa a ser verdad | `offlineQueue.ts`, `useOfflineSync.ts` | red caída en `flush` conserva la cola; 5xx igual; 409 vacía; `declaredUnknown: true` llega; 4xx a descartes; mismo `event_id` una sola vez | `cd frontend && npx vitest run src/test/hooks.useOfflineSync.test.tsx src/test/services.offlineQueue.test.ts src/test/services.offlineQueue.idb.test.ts && npx playwright test e2e/offline.spec.ts`; `cd backend && python -m pytest tests/integration/test_quiz.py -k idempotency -q` | autor de tests, implementador, verificador |
| 8 Blueprint mínimo | 42.12 | S-M | Guardar en `Track` (no en `Question`): `code`, `exam_guide`, `blueprint_version`, cargados por el loader desde el `tracks.json` existente (`content_loader.py:58-64` hoy los descarta; `content/` sin cambios); exponerlos en readiness. Proveniencia por pregunta pospuesta con el contenido (`PLAN_CONTENIDO.md:76` no se levanta) | `content_loader.py`, `models/content.py`, migración, `certification.py` | loader persiste los campos; migración con datos; readiness devuelve el bloque; `catalog_coverage.py` sin cambios | `python scripts/test_migration_data.py`; `pytest tests/content -q` | implementador, migración, verificador |
| 9 Higiene | 42.13 | S | Retirar `getPricingPlans` (`currency.ts:42-54`, sin usos; `plus: 9.99`) con test que fija los precios visibles a `plans.ts`/`prices.py`; jurisdicción de `payment_service.py:22` según H.54. Diferidos como TODO sin oleada: confianza en el cliente (`ARCHITECTURE.md:133-134`, `project.py:134-143`); eventos de analítica (`first_quiz_answer` en cada sesión, `quiz.py:795`; `role` String libre, `user.py:118`), sujetos al veto a analítica hasta ≥ 100 usuarios (fila 31.5) | `currency.ts`, `payment_service.py` | test de precios visibles | `cd frontend && npx vitest run`; `pytest tests/test_constantes_planes.py` | implementador + verificador |

## 6. Filas del ledger (literal; tras la fila 40.13, antes de `## 3.`)

```
### 41. Sincronización total de la documentación con el código y las sesiones (Oleada 0 del plan ultracode; pedido del dueño 2026-10-16; spec `PLAN_ULTRACODE.md`; prompt `PROMPT_SINCRONIZACION_DOCS.md`)

> **Estado:** `ABIERTA`. **PRI:** 0. Va antes de la serie 42. Sin contenido nuevo (ADR-62 propuesto).

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 41.1 | **0** | Liberar ≥ 6 KB del ledger (evidencias largas de DONE → `LEDGER_HISTORY.md` §T) | TODO | `check_docs.py` [8] con margen ≥ 6 KB; `ledger.py check` OK |
| 41.2 | **0** | Inventario y contraste doc ↔ código ↔ sesiones de todo el corpus vivo | TODO (tras 41.1) | `archive/verificacion/claims-<fecha>.md`: 100 % de docs con veredicto y `file:line` |
| 41.3 | **0** | Corregir en sitio las contradicciones conocidas y las nuevas | TODO (tras 41.2) | cada una con antes/después/`file:line`; `check_docs.py` verde |
| 41.4 | **0** | Una guarda en `check_docs.py` por contradicción cerrada | TODO (tras 41.3) | cada guarda: salida roja al mutar y verde al revertir, pegadas en el PR |
| 41.5 | **0** | STATUS y CHANGELOG al día; ADR-61/62/63 con cabecera; ledger al día | TODO (tras 41.3) | `ledger.py check` OK; nada reescrito hacia atrás |
| 41.6 | **0** | Escalar decisiones (H.51…H.57) y archivar el prompt ejecutado | TODO (tras 41.5) | prompt en `docs/archive/`; INVENTARIO y README al día |

### 42. Ultracode: correcciones de código tras la sincronización (oleadas 1-9; pedido del dueño 2026-10-16; spec `PLAN_ULTRACODE.md` §5)

> **Estado:** `ABIERTA`. **PRI:** 1. Sin contenido nuevo (ADR-62). Cada fila: rama + PR, test en rojo antes y en verde después, verificador §7.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 42.1 | **0** | Prueba de nivel: estimador EAP con prior; `update_ability` deja de usar la 2.ª derivada (`engine/placement.py:130-173`) | TODO (tras 41.6) | test con dificultades variadas rojo en master y verde después; simulación de la parada por SE adjunta |
| 42.2 | **0** | Puerta E2E: origen 5199 en el webServer, paso e2e en `ci_local.sh`, guarda de contrato | TODO (tras 41.6) | `npx playwright test` en local sin rojos; paso presente en `ci_local.sh` |
| 42.3 | **1** | E2E: 13 specs desfasados y causa de las 4 peticiones de `/auth` colgadas | TODO (tras 42.2) | 54 verdes o saltados con causa escrita; traza de los colgados |
| 42.4 | **1** | Duelos 3a: 202 no es «Perdiste», feedback, `leagues_opt_out`, cotas, desempate de servidor, copy asíncrono | TODO (tras 41.6) | tests rojos antes (202, opt-out, cota) y verdes después |
| 42.5 | **1** | Duelos 3b: el retador reanuda; caducidad | TODO (tras 42.4 y H.52) | test de reanudación y de tercero rechazado |
| 42.6 | **1** | Readiness sobre todas las skills del dominio, puerta de evidencia en backend, una definición de dominio | TODO (tras 42.4) | test de cobertura rojo antes; guarda de literales ampliada |
| 42.7 | **1** | `exam_pass_predictor`: retirar de `services/` o conectar tras bandera | TODO (tras H.53) | sin importadores en `backend/app`, o endpoint tras bandera con test |
| 42.8 | **1** | Prior desde el onboarding y siembra de la prueba con encogimiento | TODO (tras H.51) | placement 1/1 deja de dar 0,94; prior por experiencia con test |
| 42.9 | **1** | Evidencia por fuente: función única y contadores por fuente | TODO (tras 42.8) | `test_evidence_policy.py` por fuente; migración con datos OK |
| 42.10 | **2** | Historial de pantallas con `pushState`/`popstate`; atrás de Android | TODO | unit + e2e de pila; Android en cola humana |
| 42.11 | **1** | Offline: la cola no se vacía hasta confirmar; `declaredUnknown`; reintentos | TODO | red caída en `flush` conserva la cola; test rojo antes |
| 42.12 | **2** | Blueprint mínimo: `code`, `exam_guide`, versión en `Track` | TODO | loader persiste los campos; migración con datos OK; `content/` sin cambios |
| 42.13 | **2** | Higiene: retirar `getPricingPlans`; jurisdicción según H.54 | TODO (tras H.54) | sin usos; test de precios visibles |
```

Filas H (formato de H.50: `| H.NN | texto | Dueño |`): H.51 firmar ADR-63 y valores del
prior; H.52 duelos (opt-out de ligas ⇒ no retar ni ser retado; caducidad 7 días; sin XP por ahora;
desempate por tiempo de servidor; copy asíncrono); H.53 `exam_pass_predictor` retirar o conectar
tras bandera; H.54 ADR-61 y jurisdicción (recomendado Grecia); **H.55 deuda de contenido de
estudio** (observación del dueño: hoy el entrenamiento es por banco de preguntas, 12.037 preguntas
frente a 730 lecciones y 1.058 términos ≈ 16 preguntas por lección; opciones: lecciones largas,
ejemplos resueltos, laboratorios guiados; reabre ADR-54 «1 lección por skill»; coste a estimar;
sin diseño); H.56 promesa «Panel de equipo» del B2B; H.57 modelos (CLAUDE.md «Haiku 4.5» frente
al Haiku del entorno; CLAUDE.md prohíbe Fable y el dueño lo fijó hoy para el hilo principal).

## 7. ADR propuestos (texto que redacta la Oleada 0; el dueño firma)

- **ADR-62 — Contenido nuevo en espera por consumo de tokens; el contenido de estudio queda como
  deuda registrada** (enmienda ADR-59 y el punto «el contenido corre en paralelo» de ADR-54).
  Origen: petición del dueño 2026-10-16. Decisión: 1) hasta nueva orden no se escriben preguntas,
  lecciones ni términos ni se amplían tracks; `PLAN_CONTENIDO` y la FASE 2 punto 3 de
  `PROMPT_CONTROL_TOTAL` quedan en espera; excepción: retirar (no reescribir) un ítem con error de
  hecho; 2) la forma del catálogo (ADR-54) sigue siendo la meta; 3) deuda registrada (H.55).
- **ADR-63 — Política de evidencia por fuente y prior del onboarding** (subordinada a ADR-60
  UX-DEC-01). Contexto: una fila `UserSkillState` por (usuario, skill) escrita por práctica, duelo,
  test-out y prueba de nivel con reglas distintas; onboarding guardado (`auth.py`) pero
  `p_l0 = 0,1` fijo (`bkt.py:22`); ADR-60 define evidencia insuficiente «< 7 respuestas en el
  módulo o sin repaso diferido». Propuesta: 1) prior por experiencia
  0/1/2 → 0,10/0,20/0,30 (a calibrar), no suma intentos; 2) siembra de la prueba con encogimiento
  k=4, tope 0,94, D-18 intacto (1/1 pasa de 0,94 a 0,28; 8/8 da 0,70); 3) «dominada» = p_known ≥
  0,95 y ≥ 7 respuestas de práctica; duelo, prueba y test-out mueven p_known pero no cuentan para
  la puerta y no pasan de 0,94 por sí solos; 4) tabla por fuente (práctica: BKT sin tope, cuenta,
  FSRS; duelo: BKT, tope 0,94, no cuenta, FSRS como hoy; prueba: siembra una vez; test-out: por
  documentar leyendo `exams.py:395`; onboarding: solo prior).

## 8. Fuera de alcance

Contenido (preguntas, lecciones, términos, tracks, simulacros, todo `content/**`); el esquema de
preguntas (`PLAN_CONTENIDO.md:76`); el catálogo 35 rutas frente a 24 construidos (solo se
documenta); producción, Railway, Cloudflare, Paddle y tiendas; el texto de `docs/legal/**`; XP por
duelo; tiempo real en duelos; eventos de analítica; confianza en el cliente (TODO registrado).

## 9. Verificación de extremo a extremo

Al cerrar cada oleada: rojo pegado (tests nuevos sobre master) → verde del bucle corto →
`bash scripts/ci_local.sh` entero → pre-push sin `--no-verify` → `check_docs.py` y `ledger.py
check` verdes, ledger ≤ 61.440 B → mutación de cada guarda (roja y verde) → `git diff --name-only
origin/master | grep '^content/'` vacío → verificador §7 por fila → PR con tabla de evidencia,
filas, modelos y tokens.
Al final de todo: `bash scripts/ci_local.sh` en la rama apilada (o en master tras cada fusión del
dueño); `npx playwright test` sin rojos y con saltos justificados; `check_docs.py` verde con
[15]-[23]; `python scripts/catalog_coverage.py` con las mismas cifras de partida (24 construidos;
reservadas AIF-C01 116/130, CLF-C02 96/130, SAA-C03 2/130) como prueba de que no se tocó
contenido; `ledger.py stats` con la serie 41 en 6/6 DONE y la 42 en DONE salvo las encadenadas a
H.51-H.54; `alembic heads` con un solo HEAD igual a las tres líneas documentadas; a mano con el
dueño: 15/50 ya no da «Avanzado», un duelo a medias muestra «esperando», el atrás vuelve entre
pantallas.

## 10. Riesgos y decisiones del dueño

Riesgos: R1 ledger con 860 B de margen (41.1 primero); R2 la Oleada 0 es la más cara (~330.000
tokens de lectura única + correctores y refutadores; niveles con commit por nivel); R3 líneas y
números provisionales (re-`grep` antes de editar); R4 E2E con puertos fijos, sin runner (H.13) y
tests que quizá dependen de red; R5 el estimador nuevo cambia los niveles visibles y puede no
parar por SE (a=1 ⇒ información máxima 0,25 por ítem: se mide por simulación; θ no se persiste,
nada que migrar); R6 ADR-63 baja la maestría inicial tras la prueba y cambia tests existentes
(`test_placement.py:348,375`), sin backfill; R7 migraciones en 5 y 8 con despliegue automático
desde master; R8 cambian contratos de `/join` y `DuelAnswerResponse` (¿clientes móviles?); R9
historial frente a gestos y #215, Android sin dispositivo; R10 «79 DONE sin actualizar» sin
definir, PR #214-#216 sin leer; R11 choques de reglas (archive, históricos, dueños, legal,
`[sin verificar]`) resueltos como en el plan del dueño §2; R12 política de modelos.

Decisiones del dueño (recomendación): ADR-62 (sí); ADR-63/H.51 (prior 0,10/0,20/0,30, k=4,
puerta de 7 solo práctica); estimador EAP con prior N(0,1) y mantener 0,30/20/50 si la
simulación no para por SE; H.52 duelos; H.53 retirar `exam_pass_predictor` a `ml/`; H.54 ADR-61
como PROPUESTA y Grecia; H.55 deuda de contenido; H.56 retirar la promesa del panel (S4); H.57
no cambiar la tabla de modelos hasta confirmar; E2E como paso del nivel 2 con salida obligatoria
en el PR; no levantar `PLAN_CONTENIDO.md:76`; `@capacitor/app` solo si hace falta; S5 como dueño
de ORCHESTRATOR/PROMPT_CONTROL_TOTAL/PROTOCOLO (declarado en #89).
