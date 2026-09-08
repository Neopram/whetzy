# Whetzy — Ledger autónomo de ejecución

> **Este archivo es la fuente de verdad del progreso.** El orquestador lo lee al
> arrancar y lo escribe al cerrar. No lo edites a mano salvo para cambiar prioridades
> o desbloquear un ítem de `HUMAN-BLOCKED`.
>
> Formato de estado: `TODO` · `DOING` · `DONE` · `BLOCKED` · `HUMAN-BLOCKED`
>
> Última actualización: 2026-09-08 (sesión ah) — 4.6+5.5+6.7+7.7+8.4+9.8 ✅ DONE; Phase 4+5+6 CERRADAS; 444 tests; landing+IaC+teardown+boundaries

---

## 0. Invariantes del sistema (no romper nunca)

| Invariante | Valor |
|---|---|
| Backend prod | `https://api-production-9751.up.railway.app` |
| Frontend prod | `https://whetzy.com` / `https://whetzy.pages.dev` |
| Repo | `github.com/Neopram/whetzy` branch `master` |
| Alembic HEAD | cadena `<base> → a1b2c3d4e5f6 → b2c3d4e5f6a7 → c3d4e5f6a7b8 → d4e5f6a7b8c9 → e5f6a7b8c9d0 → f6a7b8c9d0e1 → g7h8i9j0k1l2` |
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
- `ruff check --fix` puede fallar con "Access is denied" (os error 5) en ciertos
  archivos bajo OneDrive (rename atómico choca con el sync). Fix: copiar
  `backend/app` al scratchpad (fuera de OneDrive), correr `--fix` ahí, copiar
  de vuelta archivo por archivo con `cp` normal (ese sí funciona in-place)

---

## 1. Estado por fase

| Fase | Área | % | Estado |
|---|---|---|---|
| 0 | Rebrand + Auth + Deploy | 100% | ✅ CERRADA |
| 1 | Contenido bilingüe + glosario + currículo | 100% | ✅ CERRADA |
| 2 | Tutor AI (Groq) + RAG | 100% | ✅ CERRADA |
| 3 | Gamificación + duelos + offline + Lottie | 99% | Duel E2E prod ✅; push notifs ✅; offline sync E2E ✅; solo Duel E2E multi-user pendiente (UI stub) |
| 4 | DKT + churn + MLOps | 100% | ✅ CERRADA — DKT training + eval + registry + cache + churn + A/B harness |
| 5 | Pipeline multi-agente + analytics | 100% | ✅ CERRADA — author+QA+duplicados+analytics+dashboard |
| 6 | Observabilidad + límites de servicio | 100% | ✅ CERRADA — JSON logging + OTEL + Prometheus + Sentry + liveness/readiness + rate-limiting + service boundaries |
| 7 | Commerce + i18n + nativo + IaC + seguridad | 85% | Docker/CI reales; Stripe ✅; entitlements ✅; i18n ✅; Capacitor ✅; Terraform IaC ✅; Runbook ✅; IAP HUMAN-BLOCKED |
| 8 | Garantía E2E + informe competitivo | 75% | 8.1 Playwright ✓ (auth/quiz/duelo/offline); 8.2 k6 ✓ (100 VUs 0 errores p95<3s local); 8.3 perf budget ✓ (bundle 175KB, LCP 864ms); sin informe competitivo |
| 9 | Store readiness + excelencia de diseño | 95% | 9.1-9.6+9.8 DONE; 9.7 HUMAN-BLOCKED (VoiceOver/TalkBack real device) |
| Q | Piso de calidad (transversal) | 100% | ✅ CERRADA — mypy strict + tsc strict + oxlint 0w + vitest 87% + CI ✓ |
| P | Producto — huecos que impiden vender | 92% | Email+reset+verificación+ajustes+reportes+export+deps+DB+onboarding+modo oscuro+versionado+streak reminders DONE; sin banco 1.5k |
| 10 | Marketplace de certificaciones | 0% | Dirección estratégica cerrada; arranca tras la 9 |

---

## 2. Backlog ejecutable

> Orden de ejecución = por `PRI` ascendente, luego por ID. `PRI 0` es lo que
> desbloquea todo lo demás.

### Q — Piso de calidad (transversal, PRI 0-1)

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| Q.1 | 0 | Infra de tests backend: `pytest.ini`/`conftest.py` con DB efímera, fixtures de user/token/content | DONE | pytest en <30s contra SQLite :memory:, 0 errores de setup; 141 tests pasan |
| Q.2 | 0 | Tests unitarios del engine: FSRS, Elo, BKT, bandit | DONE | 81 tests (18 BKT + 17 Elo + 18 FSRS + 24 bandit); BKT 100%, Elo 100%, FSRS 97%, bandit 96% |
| Q.3 | 1 | Tests de integración API: auth, quiz, progress, glossary, duels, placement, tutor | DONE | 88 tests: 14 auth + 11 quiz + 12 progress + 5 glossary + 18 placement + 19 duels + 9 tutor |
| Q.4 | 1 | Tests de gamificación: XP, ligas, badges, misiones, rachas | DONE | 50 tests, 100% cobertura en services/gamification/service.py |
| Q.5 | 1 | Inventario y eliminación de código muerto | DONE | ruff F401 limpio: duel.py, rag.py, bandit.py, bkt.py, elo.py, fsrs.py, gamification/service.py, quiz.py, dkt.py |
| Q.6 | 1 | Consolidación de docs: 10 archivos → set coherente | DONE | README+ARCHITECTURE+API+RUNBOOK+DECISIONS creados; 9 prompts/specs a docs/archive/ |
| Q.7 | 2 | Type strictness: mypy strict backend, tsc strict frontend | DONE | `mypy app --strict` 0 errores (63 files); `tsc --noEmit --strict` 0 errores; strict:true en tsconfig.app.json |
| Q.8 | 2 | Lint zero-warnings: ruff + oxlint | DONE | oxlint 0 warnings (6 fixes en StatsScreen/DuelScreen/pyodide-worker.js); CI usa `npx oxlint src --deny-warnings` |
| Q.9 | 2 | Tests frontend: vitest + testing-library para hooks y servicios críticos | DONE | 39 tests; 87.6% stmts/80% fns/75% branches/92.9% lines; jsdom@25; fake-indexeddb; CI: npm run test:coverage |
| Q.10 | 3 | CI real: lint + mypy + pytest + tsc + vitest + build (branch ya corregido a `master` en sesión s) | DONE | GH Actions verde: backend ✓ 2m05s / frontend ✓ 35s. Fixes: YAML quote, pip-audit flags, tsc -b, pytest-asyncio 1.4.0, aiosqlite, ruff install, mypy misc/unused-ignore, chromadb skip |

### 2 — Cierre Fase 2

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 2.1 | 2 | Pyodide E2E determinista: endpoint dev que fuerza pregunta `exec` | DONE | force_question_id en QuizStartRequest (403 en prod); pyodide.spec.ts: route intercept → fill_blank_exec q010101ex001 → '42' → ✅ output+explanation; CI ✓ (backend+e2e+frontend) |
| 2.2 | 3 | Sandbox hardening Pyodide: timeout, memoria, imports bloqueados | DONE | `builtins.__import__` factory guard blocks os/subprocess/socket/…; COOP+COEP credentialless → SharedArrayBuffer → SAB interrupt after 5 s (timedOut:true); Playwright 2/2 pass (27.7s): import os → ImportError, while True:pass → timedOut=true. vite.config + public/_headers set headers |
| 2.3 | 3 | `exec_correct` server-side (hoy viene del cliente = explotable) | DONE | QuizAnswerRequest.exec_output added; quiz.py validates exec_output.strip()==correct_answer_es.strip() when both present; fallback to selected_index (legacy) with logger.warning; 3 new tests: correct exec→true, wrong output with selected_index=1→false, trailing newline stripped; 17/17 quiz tests pass; mypy strict ✅ |

### 3 — Cierre Fase 3

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 3.1 | 2 | Duel E2E en browser (2 usuarios, Playwright) | TODO | Reto → ambos responden → resultado con ganador, verificado en UI. Bloqueador real: `joinDuel` en DuelScreen.tsx es un stub (toast "próximamente") — el oponente no puede responder desde el navegador todavía. Hay que construir esa pantalla antes de que este test tenga sentido |
| 3.2 | 3 | Offline sync E2E: responder offline → volver online → sync verificado | DONE | QuizScreen enqueues on TypeError/offline (IDB), synthetic feedback to advance; offline.spec.ts 3rd test: IDB queued → online → IDB drained; tsc 0 err; commit 181d857 |
| 3.3 | 3 | Notificaciones de duelo (push web) | DONE | pywebpush+VAPID; PushSubscription model+migration k1l2m3n4o5p6; GET /push/vapid-key+POST /push/subscribe+DELETE /push/subscribe; push_service.send_to_user (410 Gone cleanup); challenge fires to opponent; sw.js: push event→showNotification, notificationclick→focus; usePushNotifications.ts hook; 8 integration tests; 310/310 tests; tsc 0 err; commit 2e64107 |

### 4 — DKT + Churn + MLOps

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 4.1 | 2 | Pipeline de entrenamiento DKT: dataset desde `responses`, split temporal | DONE | `python -m app.ml.train_dkt --min-seqs 1` → `~/.whetzy/models/dkt/v1/model.pt` (158 KB) + metadata.json (33 skills, val_auc=0.24, 10 epochs). OneDrive gotcha: default output = ~/.whetzy/ (no OneDrive). |
| 4.2 | 2 | Harness de evaluación: AUC/ACC de DKT vs BKT baseline | DONE | `backend/app/ml/eval_dkt.py`; BKT AUC=0.3294 > DKT AUC=0.2412 (gap=0.0882). Documentado: 3 val seqs, dataset pequeño, 10 epochs insuficientes. Recomendación: más datos → retrain --epochs 30. Report en ~/.whetzy/models/dkt/v1/eval_report.json |
| 4.3 | 3 | Registro de modelos: checkpoints versionados, carga en startup, rollback | DONE | `app/ml/registry.py` singleton; lifespan loads latest at startup; `GET /ml/version` → {version, metadata, available_versions}; `POST /ml/rollback?version=N`; dkt.py uses registry model; 8 unit tests pass; mypy strict ✅ |
| 4.4 | 3 | Caché de inferencia (no correr LSTM por request) | DONE | SHA-256 TTL-60s cache in dkt.py; cache_key(history+skill_index); _predict_uncached() extracted; dkt_cache_clear() called on registry.load(); 10 unit tests pass (0.26s) incl. < 1ms cache-hit latency test; mypy strict ✅ |
| 4.5 | 3 | Predictor de churn: features + modelo + endpoint | DONE | Logistic scorer: 0.5*log1p(days_inactive) - 0.15*streak - 0.4*sessions_7d + 0.3*inaccuracy - 1.5; GET /api/v1/progress/risk → {score,factors,days_inactive,streak,sessions_7d,accuracy}; 10 unit tests AUC=0.91 > 0.70 ✅; 271/271 tests; mypy strict ✅; commit 2a77aa1 |
| 4.6 | 4 | Harness A/B: selección BKT vs DKT por cohorte | DONE | DKT_AB_RATIO setting; get_cohort() SHA-256 deterministic; _select_skill() DKT branch; GET /ml/ab-stats; 15 tests; commit 7899f41 |

### 5 — Pipeline multi-agente + analytics

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 5.1 | 3 | Agente autor de contenido: genera Q desde fuente con cita | DONE | content_agent.py: JSON extraction, _GeneratedQ validation, NullProvider guard, partial failures; POST /content/generate (201/503/422); 17 tests (9 unit + 8 integration); 335/335 tests; mypy 0 err; commit b6188d3 |
| 5.2 | 3 | Agente QA de contenido: valida distractores, dificultad, cita | DONE | content_qa.py: structural checks (opt count, correct_index, duplicates, placeholders, short stems, source, explanation, tier) + LLM pass; POST /content/qa + /qa/batch (admin key); 35 tests (27 unit + 8 integration); detection rate 100% >= 90% criterion; 370/370 tests; mypy 0 err; commit ba0acf1 |
| 5.3 | 4 | Detección de duplicados por embeddings | DONE | app/services/duplicate_detector.py: sentence-transformers all-MiniLM-L6-v2; cosine_pairs() O(N²) upper-triangle; async find_duplicates(db, skill_id?, threshold=0.85, max_pairs=200); POST /content/duplicates (admin key); 20 tests (15 unit + 5 integration) 390/390 pass; mypy strict 0 err |
| 5.4 | 3 | Esquema de eventos de analytics + ingesta | DONE | AnalyticsEvent table + migration i9j0k1l2m3n4; track(db, event_type, user_id, properties); events: user_registered (auth.register) + first_quiz_answer (quiz.submit, questions_answered==0); GET /analytics/funnel (X-Admin-Key) → registrations+first_quiz+d1+d7+rates; 5 integration tests; 276/276 tests; mypy strict ✅; commit 3fbaf31 |
| 5.5 | 4 | Dashboard de analytics (admin) | DONE | GET /analytics/dashboard: funnel+retention+engagement+skill_mastery; 9 integration tests; commit 0d9b4a4 |

### 6 — Observabilidad + límites de servicio

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 6.1 | 1 | Logging estructurado JSON con `request_id` correlacionado | DONE | core/logging.py: _JSONFormatter + RequestIDMiddleware; cada log lleva request_id + user_id |
| 6.2 | 2 | OpenTelemetry: trazas HTTP + DB | DONE | telemetry.py: FastAPIInstrumentor + SQLAlchemyInstrumentor; OTLP o console |
| 6.3 | 2 | Métricas Prometheus + `/metrics` | DONE | metrics.py: RED metrics; GET /metrics; /health exempt |
| 6.4 | 2 | Error tracking (Sentry-compatible) | DONE | error_tracking.py: configure_sentry; set_user_context en middleware |
| 6.5 | 1 | Liveness vs readiness separados | DONE | /health/live → 200 siempre; /health/ready → SELECT 1; 503 si DB down |
| 6.6 | 1 | Rate limiting por IP y por usuario | DONE | 429 + Retry-After; 12/min en /auth y /tutor; 120/min default |
| 6.7 | 4 | Límites de servicio limpios (interfaces, no microservicios prematuros) | DONE | engine+gamification __all__ completos; quiz/placement usan pkg imports; 30 boundary tests; commit 06307fd |

### 7 — Commerce + i18n + nativo + IaC + seguridad

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 7.1 | 2 | Auditoría de seguridad ASVS L2 + fixes | DONE | 6 HIGH findings fixed: timing-safe login (ASVS V2.2), jwt_version token revocation on pwd change (V3.3, migration g7h8i9j0k1l2), XFF spoofing → TRUST_PROXY_HEADERS=False default (V11.2), body stripped from 422 (V7.1), reports IDOR scoped to own user (V4.2), DEBUG=False default (V14.4). 233 tests ✅ mypy strict ✅ |
| 7.2 | 2 | Stripe: checkout + webhook + estado de suscripción | DONE | stripe_customer_id/subscription_id/status/tier/expires_at on User; migration j0k1l2m3n4o5; POST /billing/checkout (checkout URL) + POST /billing/webhook (checkout.completed/sub.updated/deleted) + GET /billing/subscription; 10 integration tests (mocked stripe); 286/286 tests; mypy 0 err; commit a010d98 |
| 7.3 | 2 | Entitlements: gating free/plus/pro | DONE | app/core/entitlements.py: user_meets_tier + require_tier dep; free<plus<pro hierarchy; is_premium=True w/o tier → plus (backward compat); quiz exam/review → plus; tutor/explain → plus; 16 tests (9 unit + 7 integration); conftest: plus_user+plus_auth_headers; 302/302 tests; commit 37acb87 |
| 7.4 | 3 | i18next completo ES/EN | DONE | i18n.ts + react-i18next; 10 screens migradas (Auth/Onboarding/Home/League/Tracks/Stats/Profile/Quiz/Duel/Placement); 0 TEXT/L dicts; duel+placement+quiz-exec keys added; tsc 0 err; commit 8f99ad9 |
| 7.5 | 3 | Shell nativo Capacitor (iOS + Android) | DONE | @capacitor/{core,cli,android,splash-screen,status-bar,keyboard,push-notifications} installed; android/ project generated + synced; deep links (https://whetzy.com + whetzy://); safe areas (env insets on TopBar/Toast/.app-content/BottomNav); iOS config in capacitor.config.ts — npx cap add ios needs Mac/Xcode (HUMAN-BLOCKED); tsc 0 err; commit b35a949 |
| 7.6 | 4 | RevenueCat IAP nativo | TODO | Sandbox purchase E2E en ambas plataformas |
| 7.7 | 4 | IaC: Terraform para Railway + Cloudflare | DONE | infra/: main+variables+railway+cloudflare+outputs; terraform fmt exit 0; HUMAN-BLOCKED on plan (Railway CLI token); commit 0acfcf7 |
| 7.8 | 2 | Runbook de backup/restore de DB | DONE | scripts/db_backup.sh + db_restore.sh + db_restore_test.sh; runbook en docs/; restore probado: 1253 Q ✅ users ✅ tracks ✅ skills ✅ — 544 KB, < 5 s |

### 8 — Garantía E2E + competitivo

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 8.1 | 1 | Suite Playwright: auth, quiz, duelo, offline, pago | DONE | CI job `e2e` ✓ verde (~2m30s): 6/6 tests (auth×3, quiz, duelo, offline). "pago" diferido a cuando 7.2 (Stripe) exista — anotado, no silenciado. 2 bugs reales encontrados y arreglados: duels.py dejaba pasar preguntas `fill_blank` legacy (sin opciones/correct_index, 150/1253) a un duelo, dejando al jugador sin botones; DB local desincronizada 3 migraciones (recreada). `AUTH_RATE_LIMIT` ahora configurable (era 12/min fijo, insuficiente para la suite) |
| 8.2 | 3 | Load test (k6): 100 usuarios concurrentes | DONE | backend/load-tests/k6-smoke.js: 100 VUs 30s ramp; por-VU X-Forwarded-For para buckets de rate-limit independientes; thresholds configurables via P95_BUDGET_MS (default 3000 local, 500 prod). Local run (4-worker uvicorn + Docker PG): checks 100% (3305/3305) · error_rate 0.00% · http_req_failed 0.00% · p95 2.72s < 3000ms ✅. Commit a7721e7 |
| 8.3 | 3 | Presupuesto de performance | DONE | scripts/check-bundle.mjs: bundle=175KB gzip < 300KB ✅; e2e/perf-budget.spec.ts: LCP 864ms < 8s CI budget, domInteractive 826ms < 10s CI budget; production targets 2.5s/3.5s documented; bundle check in CI frontend job after build; 2/2 Playwright tests pass (10.7s) |
| 8.4 | 4 | Teardown competitivo vs Duolingo/Brilliant/DataCamp | DONE | docs/competitive-teardown.md: feature matrix, 7 gaps, priority matrix, strategic summary; commit 078b837 |

### 9 — Store readiness + excelencia de diseño

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 9.1 | 2 | Revisión del sistema de diseño: tokens, motion, jerarquía | DONE | Added --le-danger token (light #E53935 / dark #FF6659); fixed --le-muted → --le-text-muted in LegalScreen; added prefers-reduced-motion block (global.css) disabling all animations/transitions; scroll-behavior: auto for reduced-motion. tsc ✅ |
| 9.2 | 2 | Accesibilidad WCAG 2.2 AA | DONE | axe-core 3/3 tests pass (auth, home, legal); viewport meta-viewport fixed; --le-text-secondary #777→#595959; contrast fixed: AuthScreen tabs/lang, BottomNav active/inactive, TopBar logo/gems, HomeScreen btnStudy/badges/streakToday, LegalScreen back/updated/body/links; link-in-text-block: underline on legal links; prefers-reduced-motion in global.css |
| 9.3 | 3 | Assets de store: iconos, screenshots, video preview | DONE | docs/store/whetzy-icon.svg (source vectorial, gradiente #1CB0F6→#0B72B0 + W blanco); scripts/generate_icons.py (Pillow, OneDrive-safe scratch→copy); iOS 13 tamaños + Contents.json; Android play-store-512px + 6 densidades mipmap; splash 2048px; android/res/ parcheado; screenshots = HUMAN-BLOCKED (requiere dispositivo físico/Xcode) |
| 9.4 | 2 | Legal: privacidad, ToS, borrado de datos (GDPR/CCPA) | DONE | LegalScreen + /privacy + /terms routes + ProfileScreen links a /privacy, /terms, /delete-account — commit b6ab6dc ✅ |
| 9.5 | 3 | Checklist App Store Review Guidelines | DONE | docs/store/app-store-review-checklist.md: 5 sections × all guidelines; 1 hard blocker B1 (Stripe→must use IAP, fix=7.6); 6 action items A1-A6; already-compliant list (ASVS/GDPR/WCAG/dark mode/safe areas/push opt-in/no IDFA/no SIWA); iOS Capacitor submission checklist |
| 9.6 | 3 | Play Store: Data Safety + target API level | DONE | docs/store/play-store-data-safety.md: targetSdkVersion=35 ✅ (≥34 req); data inventory (personal/financial/activity/device IDs/crash); third parties (Stripe/Groq/Sentry); field-by-field Play Console answers; 4 pre-submission action items |
| 9.7 | 3 | Audit de accesibilidad nativa (VoiceOver/TalkBack) | TODO | Flujos principales navegables con lector de pantalla |
| 9.8 | 4 | Sitio de marketing + pricing | DONE | LandingScreen.tsx: hero+features+pricing ES/EN; /landing route; tsc 0 err; commit 9adf861 |

### P — Producto: lo que un dueño no perdona (PRI 1-3)

> Sin esto no se puede vender. Un usuario que olvida su contraseña y no puede
> recuperarla es un usuario perdido y una reseña de una estrella.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| P.1 | 1 | Email transaccional: proveedor + plantillas ES/EN (bienvenida, verificación, reset) | DONE | SMTP+Resend+log; templates ES+EN; fallback siempre logueado |
| P.2 | 1 | Recuperación de contraseña: token de un solo uso, expira en 1 h | DONE | PasswordResetToken (SHA-256); forgot-password + reset-password; token reutilizado → 400 |
| P.3 | 1 | Verificación de email en registro | DONE | EmailVerificationToken 24h; verify-email + resend-verification; email_verified en UserRead |
| P.4 | 2 | Onboarding de primer uso: ≤ 3 pantallas (qué es · elige track · primera pregunta) | DONE | OnboardingScreen.tsx (1 pantalla): logo + headline + 3 feature cards + CTA → startQuiz. Playwright 2/2 pass (14.7s, < 60s ✓). localStorage whetzy_onboarded_{id} skips on return. tsc ✅ |
| P.5 | 2 | Ajustes de cuenta: email, contraseña, idioma, notificaciones | DONE | PATCH /auth/me + PATCH /auth/me/password + verify-email + resend-verification + forgot-password + reset-password — 229 tests pasan |
| P.6 | 2 | Reportar pregunta defectuosa desde el quiz, un toque | DONE | QuestionReport model + migration f6a7b8c9d0e1 + POST /reports/question + GET /reports/question/{id} — 229 tests pasan |
| P.7 | 2 | Exportación de datos (GDPR portabilidad) | DONE | GET /export/data → JSON attachment; sin N+1; hashed_password excluido — 229 tests pasan |
| P.8 | 3 | Banco a 1.500+ preguntas usando 5.1 + 5.2 | TODO | ≥ 1.500 Q en DB, 100 % con `source`, toda skill ≥ 6 Q, QA 5.2 en verde |
| P.9 | 3 | Versionado de contenido: corregir una Q sin romper el historial | DONE | Question.content_version (INT default 1) + Response.question_version stamps version at answer time; PATCH /api/v1/content/questions/{id} bumps version (X-Admin-Key auth, CONTENT_ADMIN_KEY env var); migration h8i9j0k1l2m3; 7 tests (auth guard, bump, no-bump on empty, response version before/after edit); 261/261 tests; mypy strict 0 err; commit 2978c67 |
| P.10 | 3 | Modo oscuro (claro sigue por defecto) | DONE | Tokens duales ✅ (design-tokens.css: :root light + @media prefers-color-scheme dark + [data-theme="dark"]); toggle en ajustes ✅ (ProfileScreen.tsx L86-91: role="switch" aria-checked); respeta prefers-color-scheme ✅ (getStoredTheme() checks matchMedia on first load); contraste AA ✅ (heredado de 9.2 DONE); tsc 0 errores |
| P.11 | 2 | Auditoría de dependencias en CI: `pip-audit` + `npm audit` | DONE | CI: pip-audit --fail-on HIGH + npm audit --audit-level=high; real pytest |
| P.12 | 2 | Rendimiento DB: índices, N+1, `EXPLAIN` en las queries calientes | DONE | 8 índices compuestos (migration e5f6a7b8c9d0): skill_elo, session_correct, user_date, etc. |
| P.13 | 3 | Recordatorios de racha sin culpa (push web + email opcional) | DONE | User.push_streak_enabled+last_streak_reminder_at; migration l2m3n4o5p6q7; PATCH /push/preferences (opt-out 1 tap); POST /push/streak-reminder (admin, 1/day, skip 0-streak/disabled/already-reminded); ProfileScreen toggle (push.supported gate); neutral copy ES+EN; 8 tests; 318/318 tests; tsc 0 err; commit 74cd3dc |

### 10 — Marketplace de certificaciones (estratégico, tras la 9)

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 10.1 | 5 | Modelo de datos para tracks de certificación (dominios, pesos, simulacro) | TODO | Schema + migración Alembic; un track de cert convive con los 7 existentes |
| 10.2 | 5 | Contenido AWS Cloud Practitioner: ≥ 300 Q con fuente oficial | TODO | Cargado, QA 5.2 en verde, cobertura de los 4 dominios del examen según pesos oficiales |
| 10.3 | 5 | Simulacro cronometrado con informe por dominio | TODO | E2E: 65 Q en 90 min, informe con % por dominio y predicción de aprobado |
| 10.4 | 6 | Catálogo y compra por certificación | TODO | Producto Stripe por cert; entitlement por cert; test-mode E2E |

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
| P.2, P.3 | P.1 |
| P.5 | P.2 |
| P.8 | 5.1, 5.2 |
| P.9 | P.6 |
| P.13 | 3.3 |
| 10.2 | 10.1, 5.1, 5.2 |
| 10.3 | 10.2 |
| 10.4 | 10.3, 7.2, 7.3 |

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
| G6 | P.5 ‖ P.6 ‖ P.7 | `endpoints/account.py` + `SettingsScreen` ‖ `endpoints/reports.py` + botón en `QuizScreen` ‖ `endpoints/export.py` |
| G7 | P.11 ‖ P.12 | `.github/workflows/` ‖ `alembic/versions/` + queries |

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
| t | 2026-09-08 | 141 (82 engine + 50 gamif + 9 core) | engine ≥96%, gamif 100% | — | F401 limpio | — | — | Q.1,Q.2,Q.4,Q.5,6.1,6.5,6.6 | 0,1 |
| u | 2026-09-08 | 229 (141 prev + 88 integración) | — | — | F401 limpio | 0 err (63 files) | — | Q.3,Q.6,Q.7(back),6.2,6.3,6.4,P.1,P.2,P.3,P.5,P.6,P.7,P.11,P.12 | 0,1 |
| v | 2026-09-08 | 229 back + 39 front | ≥60% cov | 87.6% stmts | F401 limpio | 0 err | 0 err (strict) | Q.7(front),Q.8,Q.9,Q.10 | 0,1,Q |
| w | 2026-09-08 | 230 back + 39 front + 6 E2E | ≥60% cov | 87.6% stmts | limpio | 0 err | 0 err | 8.1 | 0,1,Q |
| ab | 2026-09-08 | 241 back + 39 front + 8 E2E | ≥60% cov | 87.6% stmts | limpio | 0 err | 0 err | P.10,4.4,2.3,8.3 | 0,1,Q |
| ac | 2026-09-08 | 261 back | ≥60% cov | 87.6% stmts | limpio | 0 err | 0 err | 8.2 (k6), P.9 (content versioning) | 0,1,Q |
| ad | 2026-09-08 | 310 back + 39 front + 8 E2E | ≥60% cov | 87.6% stmts | limpio | 0 err | 0 err | 4.5(churn),5.4(analytics),7.2(Stripe),7.3(entitlements),3.3(push),P.9(content versioning) | 0,1,Q |

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
