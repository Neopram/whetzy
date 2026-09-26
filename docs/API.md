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
POST  /auth/register              → Token (201)
POST  /auth/login                 → Token (200, form-urlencoded)
POST  /auth/refresh               → Token (200)
GET   /auth/me                    → UserRead (200) 🔒
PATCH /auth/me                    → UserRead (200) 🔒  — update profile (language, display_name)
DELETE /auth/me/account           → {message} (200) 🔒
POST  /auth/logout                 → {message} (200) 🔒
PATCH /auth/me/password           → {message} (200) 🔒  — body {current_password, new_password}

POST /auth/forgot-password        → {message} (200) — no enumeration
POST /auth/reset-password         → {message} (200) — body {token, new_password}
POST /auth/verify-email           → {message} (200) — body {token}
POST /auth/resend-verification    → {message} (200)

GET  /auth/oauth/providers            → {providers: ["github"|"google"]} solo los configurados (200)
GET  /auth/oauth/{provider}/start     → 302 redirect to provider
GET  /auth/oauth/{provider}/callback  → sets cookie + redirect to frontend
```

OAuth providers: `github`, `google`.
Sign in with Apple is mandatory before any App Store submission once another OAuth provider exists (ADR-13).

## Quiz endpoints

```
POST /quiz/start                  → {session_id, question} 🔒
POST /quiz/answer                 → {correct, explanation_es, explanation_en, ...} 🔒
POST /quiz/end                    → {total, correct, xp_earned} 🔒
GET  /quiz/review-due             → {questions[], count} 🔒  — FSRS review queue
```

## Progress endpoints

```
GET  /progress/dashboard          → overall stats 🔒
GET  /progress/skills             → skill mastery list (?track_id= filter) 🔒
GET  /progress/curriculum         → module/skill tree with BKT gates (?track_id= filter) 🔒
GET  /progress/predictions        → DKT probability per skill (?track_id= filter) 🔒
GET  /progress/risk               → churn risk score 🔒
GET  /progress/decaying           → skills whose FSRS stability is decaying 🔒
```

## Placement endpoints

```
POST /placement/start             → {session_id, question} 🔒
POST /placement/answer            → next question or {finished: true, result} 🔒
GET  /placement/result            → placement result (last completed placement) 🔒
```

## Duel endpoints

```
POST /duels/challenge                → {duel_id, questions[]} 🔒
GET  /duels/my                       → list of my duels 🔒
GET  /duels/{duel_id}/join           → join a duel (returns questions) 🔒
POST /duels/{duel_id}/answer         → {answered, completed} 🔒
GET  /duels/{duel_id}/result         → {status, winner_id, scores} 🔒
```

## Tutor endpoint

```
POST /tutor/explain               → {explanation, provider, grounded, context_used} 🔒 — Pro: 429 `tutor_daily_limit` after `TUTOR_DAILY_LIMIT_PLUS`/day UTC; Pro Max unlimited (38.6)
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
POST /exams/module/{module_id}/test-out/start → module test-out (17.2)
POST /exams/track/{attempt_id}/submit       → per-skill report + verdict + certificate

GET  /exams/certification/{track_id}/readiness → readiness score + domain gaps 🔒
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

## Lessons endpoints

```
GET  /lessons/{skill_id}   → {skill_id, lesson_es, lesson_en, example_code} 🔒
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
POST /billing/checkout     → {checkout_url} 🔒  — Stripe checkout session
GET  /billing/subscription → {plan, status, renews_at} 🔒
POST /billing/webhook      → Stripe webhook (unsigned traffic rejected by HMAC)
```

## Session & 2FA endpoints

```
GET  /auth/sessions                      → [{id, device, ip, last_seen}] 🔒
POST /auth/sessions/{session_id}/revoke  → {revoked} 🔒 — cierra esa sesión
POST /auth/2fa/setup                     → {secret, qr_uri} 🔒 — TOTP, aún sin activar
POST /auth/2fa/enable                    → {enabled} 🔒 — confirma con un código válido
POST /auth/2fa/verify                    → {verified} 🔒
```

## Economy endpoints

Créditos por lotes FIFO con caducidad; el saldo se deriva sumando el ledger, no
se guarda en ninguna columna.

```
GET  /economy/prices            → {credit_value_usd, grifos[], sumideros[]} — público
GET  /economy/balance           → {balance, currency, expires_in_days} 🔒
GET  /economy/referral/code     → {code, share_url} 🔒 — lo crea si no existe
POST /economy/promo/redeem      → {credits, balance, message} 🔒 — solo web (X-Platform ios/android → 403); rate limit 5/10 min por usuario
POST /economy/referral/activate → {activated, referrer_id} 🔒
GET  /economy/streak-freeze     → {price, balance, held, max_held, purchases_this_week, max_per_week, can_buy, blocked_by} 🔒 — comodín de racha (35.3)
POST /economy/streak-freeze     {request_id: uuid} → mismo cuerpo + {replayed} 🔒 — compra con créditos; 409 `insufficient_credits` · `max_held` · `weekly_limit`; el mismo `request_id` nunca cobra dos veces
```

## Instructor marketplace endpoints

Reparto 70/30 tras la comisión de Paddle (7,5 %) y la retención del 22 % que fija
H.29. El pago se acumula en una fila por instructor y mes, no una por matrícula.

```
POST /instructor/courses                     → {id, …} 🔒 — publicar curso
GET  /instructor/courses                     → [{…}] 🔒
POST /instructor/courses/{course_id}/enroll  → {enrollment_id, payout_id, desglose} 🔒 — sin body: el importe es `price_cents` del curso; 403 si no está `published`, 409 si ya inscrito. Sin pasarela no cobra (Paddle HUMAN-BLOCKED)
GET  /instructor/analytics                   → {total_earnings_cents, …} 🔒
GET  /instructor/payouts                     → [{period_start, earnings_cents, …}] 🔒
```

## Experiment endpoints

```
GET /experiments/flags → {"nombre_del_experimento": "A" | "B"} 🔒
```

La variante sale de un hash de (experimento, usuario), no de un sorteo: el mismo
usuario cae siempre del mismo lado aunque se pierda la fila.

## Webhook endpoints

```
POST /webhooks/paddle → {received} — público, firma HMAC-SHA256 en X-Signature
```

Sin `PADDLE_API_KEY` configurada **rechaza** con 401. Falla cerrado a propósito:
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
GET  /admin/economy/referrals            → referral program analytics
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
| `/api/v1/auth/*` | 12 req/min per IP |
| `/api/v1/tutor/*` | 12 req/min per IP |
| All other routes | 120 req/min per IP |

429 responses include `Retry-After` header.

## Route count

111 paths (107 under `/api/v1/` + 4 root: `/`, `/health`, `/health/live`, `/health/ready`).
Some paths have multiple HTTP methods, giving **114 method+path endpoints** total.
Verified locally: `python -c "from app.main import app; spec=app.openapi(); print(sum(len(v) for v in spec['paths'].values()))"`.




