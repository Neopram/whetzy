# Whetzy — API Reference

Full interactive spec: `/api/v1/openapi.json` (dev: http://localhost:8000/docs)

## Conventions

- Base path: `/api/v1`
- Auth: `Authorization: Bearer <access_token>` on all protected routes
- Login uses **form-urlencoded** (OAuth2): `Content-Type: application/x-www-form-urlencoded`
- All other requests use JSON
- `POST /auth/register` → 201 with `{access_token, refresh_token}`
- `POST /auth/login` (form-urlencoded: `username`=email, `password`) → 200 with tokens

## Gotchas

| Endpoint | Gotcha |
|---|---|
| `POST /auth/login` | Uses form-urlencoded, not JSON |
| `POST /quiz/start` | Returns `{session_id, question: {id, ...}}` — `question_id` is at `.question.id` |
| `POST /quiz/answer` | `session_id` is in the **JSON body**, not the URL path |
| `POST /placement/start` | `session_id` is returned in the body; pass it in the body of subsequent calls, not the URL |
| `POST /duels/{id}/answer` | Requires `selected_index` + `response_time_ms` |
| `POST /duels/challenge` | Returns `questions[]` not `question_ids[]` |
| `GET /glossary/{track_id}` | `track_id` is a string (`"track01"`), not an int |

## Auth endpoints

```
POST  /auth/register              → Token (201)  — manda un solo correo, el de verificación (`/verify-email?token=…&lang=es|en`); la bienvenida no (45.2, ADR-66 E2)
POST  /auth/login                 → Token | {mfa_required, mfa_token} (200, form-urlencoded) — con 2FA activada no abre sesión: devuelve el reto (5 min) para `/auth/2fa/login`
POST  /auth/refresh               → Token (200)
GET   /auth/me                    → UserRead (200) 🔒
PATCH /auth/me                    → UserRead (200) 🔒  — update profile (language, display_name, onboarding answers,
                                     target_track_id, target_certification_id — certification tracks only, else 422 —
                                     and onboarding_completed: true, which sets onboarding_completed_at once; 43.3)
DELETE /auth/me/account           → {message} (200) 🔒
POST  /auth/logout                 → {message} (200) 🔒  — sube `jwt_version` (41.18): cualquier access/refresh emitido antes queda inválido, igual que ya hace el cambio de contraseña
PATCH /auth/me/password           → {message} (200) 🔒  — body {current_password, new_password}

POST /auth/forgot-password        → {message} (200) — no enumeration
POST /auth/reset-password         → {message} (200) — body {token, new_password}
POST /auth/verify-email           → {message} (200) — body {token}; la primera vez que verifica la cuenta manda la bienvenida, una sola vez (45.2). OAuth la manda al crear la cuenta, que ya llega verificada
POST /auth/resend-verification    → {message} (200)

GET  /auth/oauth/providers            → {providers: ["github"|"google"]} solo los configurados (200)
GET  /auth/oauth/{provider}/start     → 302 redirect to provider (`?lang=es|en` opcional) — PKCE (S256) + cookie HttpOnly con el `state` (41.14); `lang` va en otra cookie corta y solo se usa si el callback **crea** la cuenta (45.1, ADR-66 E1; uno no válido se ignora)
GET  /auth/oauth/{provider}/callback  → sets cookie + redirect to frontend — 400 si la cookie del `state` no coincide con el de la query (41.14)
```

OAuth providers: `github`, `google`.
Sign in with Apple is mandatory before any App Store submission once another OAuth provider exists (ADR-13).

## Quiz endpoints

```
POST /quiz/start                  → {session_id, question} 🔒
POST /quiz/answer                 → {correct, explanation_es, explanation_en, ...} 🔒 — body: session_id, question_id, response_time_ms y, según el tipo, selected_index (opciones), exec_output (fill_blank_exec, fix_bug, sql_exec, js_exec: la salida que dio el código) o answer_text (fill_blank: lo escrito; se compara recortado y sin mayúsculas) o widget_state (interactive, 40.1: el estado serializado del widget, ≤ 20.000 caracteres en JSON; el servidor lo corrige con el checker de la pregunta, `exact` o `unordered`). Sin exec_output/answer_text/widget_state la respuesta es incorrecta: el servidor no cree al cliente. `widget_target` (interactive): el objetivo, solo ya respondida, para que el cliente vuelva a corregir; null en los demás tipos. La pregunta servida trae `interactive: {widget, params, checker}`, sin `target`. `events[]` (46.1b): hitos que cruzó esa respuesta, cada uno una vez — `level_up {level_before, level}`, `badge_earned {badge_id}`, `mission_completed {mission_id}`, `combo_multiplier {multiplier: 2|3|5}` (al llegar el combo a 3, 7 o 15) y `streak_milestone {days: 7|30|100}`; vacío en la reentrega idempotente de un `event_id`
POST /quiz/end                    → {total_questions, correct, accuracy, max_combo, xp_earned, duration_seconds, credits_earned} 🔒 — `credits_earned`: lo que la sesión dejó ganado (módulo, racha, diagnóstico; ECONOMIA §2.2)
GET  /quiz/review-due             → {questions[], count} 🔒  — FSRS review queue
```

## Progress endpoints

```
GET  /progress/dashboard          → overall stats 🔒
GET  /progress/skills             → skill mastery list (?track_id= filter) 🔒
GET  /progress/curriculum         → module/skill tree with BKT gates (?track_id= filter); per skill `lesson_seen`
                                     (lesson opened) and `practice_unlocked` (lesson seen, passed test-out or a module
                                     with a head start in the placement test; 43.5, ADR-65 D7/H.60) 🔒
GET  /progress/predictions        → DKT probability per skill (?track_id= filter) 🔒
GET  /progress/risk               → churn risk score 🔒
GET  /progress/decaying           → skills whose FSRS stability is decaying (?track_id= filter, 43.4) 🔒
GET  /progress/thresholds         → canonical domain thresholds (mastery, module unlock) 🔒
```

## Placement endpoints

```
POST /placement/start             → {session_id, question} 🔒
POST /placement/answer            → next question or {finished: true, result} 🔒  — exactly 20 questions (43.3, ADR-65 D3):
                                     5 basic, 5 intermediate, 5 advanced, then 5 in the frontier band; on finish it seeds
                                     p_known per module (D4: ≥ 70 % of ≥ 2 → 0.6, else shrunk toward 0.1; never lowers history)
GET  /placement/result            → placement result (last completed placement) 🔒
```

## Duel endpoints

```
POST /duels/challenge                → {duel_id, questions[]} 🔒  — 409 {code: needs_lesson | opponent_needs_lesson}
                                     when either player can't practise the skill yet (43.5, D7)
GET  /duels/my                       → list of my duels 🔒
GET  /duels/{duel_id}/join           → join a duel (returns questions) 🔒
POST /duels/{duel_id}/answer         → {answered, completed} 🔒
GET  /duels/{duel_id}/result         → {status, winner_id, scores} 🔒
```

## Moderation endpoints

Reportar es un registro para que el dueño lo revise, sin cola ni acción
automática. Bloquear es bidireccional: `duels.py` rechaza el reto (403) entre
cualquiera de las dos direcciones, y las ligas ocultan a cada bloqueado de la
liga del otro (19.11).

```
POST   /moderation/report            → {id, reported_id, reason, context, created_at} 🔒 — reason: inappropriate_name|harassment|spam|other
POST   /moderation/block             → {user_id, username, display_name, blocked_at} 🔒 — idempotente
DELETE /moderation/block/{user_id}   → 204 🔒
GET    /moderation/blocked           → [{user_id, username, display_name, blocked_at}] 🔒
```

## Tutor endpoint

```
POST /tutor/explain               → {explanation, provider, grounded, context_used} 🔒 — Pro: 429 `tutor_daily_limit` after `TUTOR_DAILY_LIMIT_PLUS` explanations OR `TUTOR_DAILY_TOKEN_LIMIT_PLUS` tokens/day UTC (41.17, engineering backstop, never applies to the ADR-49-unlimited tiers); Pro Max unlimited (38.6). Quota reserved atomically before LLM call, settled to real token count after. 403 `question_reserved` for a `pool == "simulacro"` question, 403 `exam_in_progress` for one in an unsubmitted `MockExamAttempt` of the caller's (41.5). No cupo cuando un `GuardedProvider` configurado cae en el `NullProvider` por dentro (presupuesto agotado o la cadena entera falla) — sí cuando `get_provider()` ya es `NullProvider` a secas (sin API key)
  Body: {question_id, conversation_history?: [...]}
```

## Exam endpoints

Three kinds of sitting share one table and one clock. They differ in how they
are blueprinted and in what passing earns.

```
POST /exams/mock/start                      → certification mock (10.3), body {track_id}
POST /exams/mock/{attempt_id}/submit        → per-domain report; pass/fail + certificate only for a certifying sitting
GET  /exams/mock/{attempt_id}               → rereads a graded attempt

GET  /exams/track/{track_id}/blueprint      → questions, minutes, pass mark (before committing)
POST /exams/track/{track_id}/start          → course final exam (17.2)
GET  /exams/module/{module_id}/test-out/blueprint → {module_id, skills, questions, duration_minutes, pass_pct, available} — available=false si alguna skill no tiene preguntas para montarla (start respondería 400); 404 si el módulo no existe
POST /exams/module/{module_id}/test-out/start → module test-out (17.2)
POST /exams/track/{attempt_id}/submit       → per-skill report + verdict + certificate

GET  /exams/certification/{track_id}/readiness → readiness score + domain gaps (domain mean over every skill, unassessed = 0; 43.4) 🔒
GET  /exams/certification/{track_id}/access    → price, paywall on/off, purchased, can_start (38.7) 🔒
POST /exams/certification/{track_id}/start     → certifying exam: mock blueprint + Whetzy pass mark (38.7) 🔒
GET  /exams/certificates/{code}             → PUBLIC, no auth
GET  /exams/certificates/{code}/badge      → Open Badges 3.0 JSON-LD (29.10), PUBLIC
GET  /exams/certificates/{code}/qr         → QR code PNG for verification URL (29.10), PUBLIC
```

| Endpoint | Gotcha |
|---|---|
| `POST /exams/track/{...}/submit` | The path parameter is the **attempt id**, not the track id |
| `POST /exams/track/{track_id}/start` | 400 on a certification track — use `/exams/mock/start` instead |
| `POST /exams/mock/{...}/submit` | Never a scaled score. A plain mock has no pass; a certifying sitting (`kind=certifying`) adds `passed`, `pass_pct`, `pass_note_*` and, if passed on time, `certificate` |
| `POST /exams/certification/{track_id}/start` | 402 `certification_purchase_required` only with `CERTIFICATION_PAYWALL=true` and no purchase; one purchase covers every retake (ADR-49) |
| Certification mock `pass_pct` | `null` — only `track_final` and `test_out` carry a pass mark |
| Late submission | Still graded but `status` becomes `expired` and earns **no** certificate |
| `GET /exams/certificates/{code}` | **Unauthenticated**: the 128-bit code is the only key |
| `GET /exams/certificates/{code}/badge` | Returns `application/ld+json`; signed with Ed25519 only when `OB_SIGNING_PRIVATE_KEY` is set |
| `GET /exams/certificates/{code}/qr` | Returns `image/png`; encodes `whetzy.com/verify/{code}` |
| Certificate uniqueness | One per (user, track); re-sitting returns the same code |

## Glossary endpoints

```
GET  /glossary/{track_id}  → [{term_es, term_en, definition_es, definition_en}]
```

`track_id` is a string like `"track01"`. Unauthenticated.

## Public profile endpoint

```
GET  /profiles/{username}  → {username, display_name, avatar_emoji, joined_at, current_streak, mastery_avg, skills_mastered, certificates: [{code, track_name_es, track_name_en, issued_at}], projects_completed: [{slug, name_es, name_en, completed_at}]}  PUBLIC, no auth
```

404 for an unknown or inactive `username` (0.3), and always while `PUBLIC_PROFILES_ENABLED` is false (default) — no privacy opt-out column yet
(same shape as `GET /exams/certificates/{code}`, unauthenticated by the same
logic: a public identifier is enough). `mastery_avg`/`skills_mastered` come
from `UserSkillState`/`MASTERY_THRESHOLD`; `certificates` excludes revoked;
`projects_completed` only lists `ProjectSubmission.completed=true`.

## Bootcamp endpoints

```
GET  /bootcamps                    → [{id, slug, name_es, name_en, description_es, description_en, duration_weeks, daily_goal_minutes, icon, color, order}]
GET  /bootcamps/{slug}             → {…bootcamp, weeks: [{id, week_number, track_id, title_es, title_en}]}
POST /bootcamps/{slug}/enroll      → {id, bootcamp_id, started_at, current_week, completed_at} 🔒  201 | 409 already enrolled
GET  /bootcamps/{slug}/progress    → {id, bootcamp_id, started_at, current_week, completed_at} 🔒  404 if not enrolled
```

List and detail are unauthenticated; enroll and progress require login.

## Projects endpoints

```
GET  /projects                         → [{id, slug, track_id, runtime, name_es, name_en, description_es, description_en, difficulty, source_url, source_license, order}]  ?track_id=&runtime=
GET  /projects/{slug}                  → {…project, steps: [{id, step_number, title_es, title_en, instructions_es, instructions_en, starter_code, test_code}]}
POST /projects/{slug}/start            → {id, project_id, current_step, completed, started_at, completed_at} 🔒  201 | 409 already started
GET  /projects/{slug}/progress         → {id, project_id, current_step, completed, started_at, completed_at} 🔒  404 if not started
POST /projects/{slug}/submit-step      → {id, project_id, current_step, completed, started_at, completed_at} 🔒  body: {step_number, passed}
```

List and detail are unauthenticated; start, progress and submit-step require login.

## Lessons endpoints

```
GET  /lessons/{skill_id}   → {skill_id, lesson_es, lesson_en, example_code} 🔒  — records the lesson as seen; since
                            43.5 practising (study/review) a skill requires it, a passed test-out or placement head start
```

## Badges & missions endpoints

```
GET  /badges               → user's earned badges 🔒
GET  /missions             → active missions + progress 🔒
```

## League endpoints

```
GET  /league/current       → current week's league standings 🔒
GET  /league/history       → past league results for current user 🔒
PUT  /league/participation {participate: bool} → current standings + {participating} 🔒 — ligas opcionales (35.4): fuera, `standings` vacío y nadie te ve; XP, nivel y racha siguen
```

## Reports endpoints

```
POST /reports/question                      → submit a broken-question report 🔒
GET  /reports/question/{question_id}        → get reports for a question (admin) 🔒
```

Admin routes require `X-Admin-Key` header.

## Push notification endpoints

```
GET    /push/vapid-key            → {public_key} — VAPID public key for ServiceWorker
POST   /push/subscribe            → subscribe to web push 🔒
DELETE /push/subscribe            → unsubscribe 🔒
PATCH  /push/preferences          → update notification preferences 🔒
POST   /push/streak-reminder      → trigger a streak reminder (debug/admin) 🔒
```

## ML endpoints

```
GET  /ml/version           → {version, accuracy, deployed_at} — current model info
GET  /ml/ab-stats          → A/B cohort stats (BKT vs DKT) (admin)
POST /ml/rollback          → roll back to previous model version (admin)
```

Admin routes require `X-Admin-Key` header.

## Analytics endpoints

```
GET  /analytics/dashboard  → funnel + retention dashboard (admin)
GET  /analytics/funnel     → per-step funnel counts (admin)
```

Admin routes require `X-Admin-Key` header.

## Billing endpoints

```
POST /billing/checkout     → {checkout_url} 🔒  — Stripe checkout session (accepts eu_withdrawal_waiver: bool). **Sin uso:** el dueño descartó Stripe (H.29); la web paga con Paddle en `/checkout`
GET  /billing/subscription → {is_premium, subscription_status, subscription_tier, subscription_provider, stripe_customer_id, stripe_subscription_id} 🔒 — subscription_provider: "stripe" | "revenuecat" | "paddle" | null
POST /billing/webhook      → Stripe webhook (unsigned traffic rejected by HMAC). **Sin uso** (H.29)
POST /billing/revenuecat/webhook → RevenueCat webhook (17.14, mobile IAP, sandbox) — Authorization header secret, 503 until REVENUECAT_WEBHOOK_AUTHORIZATION is set
GET  /billing/paddle/config → {enabled, environment, client_token, prices{plus,pro,certification,plus_annual,pro_annual}} — público: lo que la web necesita para abrir Paddle.js (H.29); enabled=false hasta configurar PADDLE_CLIENT_TOKEN y un precio
POST /billing/paddle/cancel → {cancel_requested, access_until} 🔒 — cancela la suscripción de Paddle al final del periodo pagado (H.29); 404 si no tiene una, 502 si Paddle no la acepta. El estado lo escribe el webhook
```

## Session & 2FA endpoints

```
GET  /auth/sessions                      → [{id, device, ip, last_seen}] 🔒
POST /auth/sessions/{session_id}/revoke  → {revoked} 🔒 — cierra esa sesión
GET  /auth/2fa/status                    → {enabled, backup_codes_left} 🔒
POST /auth/2fa/setup                     → {secret, qr_uri, qr_svg, backup_codes[10]} 🔒 — TOTP, aún sin activar; 409 `2fa_already_enabled` si ya está activa (rehacer el alta la apagaría sin código)
POST /auth/2fa/enable                    → {message} 🔒 — confirma con un código válido; 400 si no lo es
POST /auth/2fa/disable                   → {enabled: false} 🔒 — exige `{code}` (TOTP o de respaldo); 400 si no vale
POST /auth/2fa/verify                    → {verified} 🔒
POST /auth/2fa/login                     → Token — segundo paso del login: `{code, mfa_token?}`; sin `mfa_token` lo lee de la cookie HttpOnly `whetzy_mfa` (vuelta de OAuth a `/auth?mfa=1`). 400 código malo, 401 reto caducado, 429 bloqueo por intentos
```

## Economy endpoints

Créditos por lotes FIFO con caducidad; el saldo se deriva sumando el ledger, no
se guarda en ninguna columna.

```
GET  /economy/prices            → {credit_value_usd, grifos[], sumideros[], learning_monthly_cap} — público; solo lo cableado (referidos con `milestones`; diagnóstico, módulo, skill saltada, rachas de 7 y 30 días; comodín de racha e informe de dominio)
GET  /economy/balance           → {balance, currency, expires_in_days} 🔒 — días hasta que caduque el primer lote con saldo (0 = nada)
GET  /economy/referral/code     → {code, share_url} 🔒 — lo crea (y lo guarda) si no existe
POST /economy/promo/redeem      → {credits, balance, message} 🔒 — solo web (X-Platform ios/android → 403); rate limit 5/10 min por usuario
GET  /email/unsubscribe         → página HTML — público, `?token=`; baja de los correos de ofertas (el enlace del correo)
POST /email/unsubscribe         → {unsubscribed} — público, `?token=`; «One-Click» de RFC 8058 (Gmail, Yahoo)
PATCH /email/preferences        {marketing: bool} → {marketing} 🔒 — interruptor de Yo → Ajustes
POST /economy/referral/activate → {activated, referrer_id} 🔒 — registra el referido (`pending`) y le da 200 créditos; activación y abono, en `referral_program_loop` (ADR-57)
GET  /economy/streak-freeze     → {price, balance, held, max_held, purchases_this_week, max_per_week, can_buy, blocked_by} 🔒 — comodín de racha (35.3)
POST /economy/streak-freeze     {request_id: uuid} → mismo cuerpo + {replayed} 🔒 — compra con créditos; 409 `insufficient_credits` · `max_held` · `weekly_limit`; el mismo `request_id` nunca cobra dos veces
POST /mastery-reports           {request_id: uuid} → 201 {code, created_at, snapshot} 🔒 — informe de dominio (ECONOMIA §2.3): cobra 300 créditos; el mismo `request_id` devuelve el mismo informe sin cobrar; 409 `insufficient_credits`
GET  /mastery-reports           → {reports: [{code, created_at}]} 🔒 — los míos
GET  /mastery-reports/{code}    → {code, created_at, snapshot} — PÚBLICO, sin sesión, como un certificado: instantánea con fecha (nombre y usuario públicos, dominio por ruta, skills dominadas, precisión, racha máxima; sin email)
```

## Instructor marketplace endpoints

Reparto 80/20 (ADR-41; `payment_service.INSTRUCTOR_SHARE`) tras la comisión de Paddle (7,5 %) y la retención del 22 % que fija
H.29. El pago se acumula en una fila por instructor y mes, no una por matrícula.

```
POST  /instructor/courses                     → {id, …} 🔒 — publicar curso
GET   /instructor/courses                     → [{…}] 🔒
POST  /instructor/courses/{course_id}/enroll  → {enrollment_id, payout_id, desglose} 🔒 — sin body: el importe es `price_cents` del curso; 403 si no está `published` o es tu propio curso, 409 si ya inscrito, **402 siempre que `price_cents > 0`** (41.6): no existe ningún producto Paddle de curso (Paddle HUMAN-BLOCKED), así que no hay manera de confirmar el cobro — antes de esto se inscribía gratis y aun así creaba un `InstructorPayout` real
GET   /instructor/analytics                   → {total_earnings_cents, …} 🔒
GET   /instructor/payouts                     → [{period_start, earnings_cents, …}] 🔒
GET   /instructor/profile                     → {display_name, bio, avatar_url, website} 🔒 — se crea el instructor si el usuario aún no lo era (28.8: `ProfileTab` no llamaba a nada)
PATCH /instructor/profile                     → {display_name, bio, avatar_url, website} 🔒 — todos los campos opcionales, solo se actualiza lo enviado
```

## Experiment endpoints

```
GET /experiments/flags → {"nombre_del_experimento": "A" | "B"} 🔒
```

La variante sale de un hash de (experimento, usuario), no de un sorteo: el mismo
usuario cae siempre del mismo lado aunque se pierda la fila.

## Webhook endpoints

```
POST /webhooks/paddle → {received} — público; Paddle Billing: cabecera Paddle-Signature (ts=..;h1=..), HMAC-SHA256 de "ts:cuerpo" con PADDLE_WEBHOOK_SECRET, 5 s de tolerancia; 401 firma mala, 503 sin secreto, 500 si falla al procesar (Paddle reintenta)
```

Sin `PADDLE_WEBHOOK_SECRET` configurado **rechaza** con 503. Falla cerrado a propósito:
lo que no se puede verificar no se acepta.

## Content endpoints (admin)

All content routes require `X-Admin-Key` header.

```
GET   /content/tracks                       → all tracks with stats
PATCH /content/questions/{question_id}      → versioned edit (bumps content_version)
POST  /content/generate                     → LLM author agent — generate questions
POST  /content/qa                           → run QA checks on a question
POST  /content/qa/batch                     → batch QA pass
POST  /content/duplicates                   → embedding-based duplicate detection
```


## Admin endpoints

All admin routes require `X-Admin-Key` header.

### Instructor moderation (28.6)
```
GET   /admin/instructor/courses                      → paginated course list with instructor info 🔒 admin — ?status=draft|published|archived|rejected &page= &per_page=
PATCH /admin/instructor/courses/{course_id}/status   → approve/reject/archive a course 🔒 admin — ?new_status=published|rejected|archived|draft
GET   /admin/instructor/payouts                      → paginated payout list 🔒 admin — ?status=pending|processing|completed|failed &page= &per_page=
PATCH /admin/instructor/payouts/{payout_id}/status   → process/complete/fail a payout 🔒 admin — ?new_status=pending|processing|completed|failed
```

### Content management
```
GET  /admin/content/gaps                 → gaps in question coverage
GET  /admin/content/parity               → parity check across languages
```

### Correo (H.30)
```
GET  /admin/email/status                 → {provider, configured, from, …} 🔒 owner — si el correo sale y por dónde; nunca devuelve la clave
POST /admin/email/test                   → {sent, provider, to} 🔒 owner — envía de verdad (query `to`, por defecto el propio owner); 503 con el motivo del proveedor si falla
```

### Economy & credits
```
GET  /admin/economy/credits              → credit summary (emitted/spent/expired, sink/source ratio, inflation alert) + ledger rows
GET  /admin/economy/k-factor             → K-factor statistics
GET  /admin/economy/referrals            → referral program analytics — ?status=all|pending|activated|credited|rejected|clawed_back
POST /admin/economy/referrals/{referral_id}/clawback → {recovered_credits, unrecovered_credits, milestone_revoked} 🔒 admin — `{reason: refund|ban|fraud}`; recupera lo que quede de los 300 sin saldo negativo y retira el premio del hito si se baja de él (ECONOMIA §3.5); 404 si no existe, 409 si ya estaba cerrado
GET  /admin/reports/recent               → {reports[]} ?limit&reason — reportes de alumnos con su nota (incluye `ai_explanation`)
GET  /admin/economy/scorecard            → 5 KPI metrics vs m3/m6/m12 targets (ECONOMIA.md §7) 🔒 admin — ?segment=all|es|en &days=30
POST /admin/promo/batch ?code_type&credits&count&max_uses&language&campaign_id&expires_days → {count, codes[], csv} — genera lote de códigos promocionales; tipos: onboarding|campaign|reactivation|referral_bonus|instructor; alfabeto seguro sin 0OIL1
```

### GDPR & user management
```
GET  /admin/gdpr/deletions               → pending deletion requests
GET  /admin/gdpr/exports                 → pending data export requests
POST /admin/gdpr/deletions/{user_id}/cancel → cancel deletion request
```

### Metrics & analytics
```
GET  /admin/metrics/funnel               → conversion funnel metrics
GET  /admin/metrics/ttfq                 → time-to-first-question metrics
GET  /admin/metrics/users                → user engagement metrics
GET  /admin/metrics/engagement           → quiz sessions, accuracy, retention D30, duels, top skills 🔒 admin
GET  /admin/metrics/reports              → question reports summary by reason + most reported 🔒 admin
```

### Operations
```
GET  /admin/ops/database                 → database health & stats
GET  /admin/ops/deploy-info              → Alembic head, app version, Railway deployment 🔒 admin
GET  /admin/ops/errors                   → recent error logs
GET  /admin/ops/health                   → system health status
GET  /admin/ops/tutor-usage              → per-user and per-day tutor explanation counts 🔒 admin
```

### KPI Dashboard
```
GET  /admin/kpi/dashboard                → consolidated KPIs with M3/M6/M12 objectives 🔒 owner
```

### Revenue
```
GET  /admin/revenue/churn                → churn analysis
GET  /admin/revenue/conversions          → conversion funnel (trial → paid)
GET  /admin/revenue/mrr                  → monthly recurring revenue
```

### Security
```
GET  /admin/security/auth-events         → authentication event log
GET  /admin/security/ip-analysis         → IP reputation & geo analysis
GET  /admin/security/lockouts            → account lockout events
GET  /admin/security/rate-limit-hits     → rate-limit denial stats (22.1)
```
## Export endpoints

```
GET  /export/data          → GDPR data export (JSON) 🔒
```

## Privacy endpoints (21.3)

```
POST   /privacy/ccpa-opt-out      → Record CCPA "Do Not Sell/Share" opt-out 🔒
DELETE /privacy/ccpa-opt-out      → Revoke CCPA opt-out (opt back in) 🔒
GET    /privacy/ccpa-disclosure   → CCPA data-collection disclosure (§1798.100) — public
GET    /privacy/rights            → Jurisdiction-aware privacy rights summary — public
```

## Newsletter endpoints

```
POST /newsletter/subscribe      {email, language?} → 202 {status} — público; crea sin confirmar y manda el correo; misma respuesta exista ya el email o no, y si está dentro del enfriamiento de reenvío (5 min)
GET  /newsletter/confirm        → página HTML — público, `?token=&lang=`; solo muestra el botón, no confirma (así lo sigue un escáner de enlaces sin confirmar nada)
POST /newsletter/confirm        → página HTML — público, `?token=`; confirma — lo dispara el botón de la página de arriba
GET  /newsletter/unsubscribe    → página HTML — público, `?token=&lang=`; solo muestra el botón, no da de baja
POST /newsletter/unsubscribe    → página HTML — público, `?token=`; da de baja — el botón, y también «One-Click» de RFC 8058 (Gmail, Yahoo)
```

## Health endpoints

```
GET  /health/live    → {status: "ok"} — liveness probe (always 200)
GET  /health/ready   → {status: "ready"} — readiness probe (503 if DB down)
GET  /health         → {status: "healthy"}
GET  /              → {name, status, version}
```

## Rate limits

| Path prefix | Limit |
|---|---|
| `/api/v1/auth/{login,register,forgot-password,reset-password,resend-verification,verify-email,oauth,2fa}*` | 60 req/min per IP (`AUTH_RATE_LIMIT`) |
| `/api/v1/tutor/*` | 60 req/min per IP (`AUTH_RATE_LIMIT`) |
| All other routes | 120 req/min per IP |

429 responses include `Retry-After` header.

## Route count

164 paths (160 under `/api/v1/` + 4 root: `/`, `/health`, `/health/live`, `/health/ready`).
Some paths have multiple HTTP methods, giving **174 method+path endpoints** total.
Verified locally on `claude/ultracode-0-docs-sync` (base `0de27ad`):
`python -c "from app.main import app; spec=app.openapi(); print(len(spec['paths']), sum(len(v) for v in spec['paths'].values()))"`
→ `164 174`.




