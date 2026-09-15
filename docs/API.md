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
| `POST /duels/{id}/answer` | Requires `selected_index` + `response_time_ms` |
| `POST /duels/challenge` | Returns `questions[]` not `question_ids[]` |
| `GET /api/v1/glossary/track/{track_id}` | `track_id` is a string (`"track01"`), not an int |

## Auth endpoints

```
POST /auth/register              → Token (201)
POST /auth/login                 → Token (200, form-urlencoded)
POST /auth/refresh               → Token (200)
GET  /auth/me                    → UserRead (200) 🔒
DELETE /auth/me/account          → {message} (200) 🔒

POST /auth/forgot-password       → {message} (200) — no enumeration
POST /auth/reset-password        → {message} (200)
POST /auth/verify-email          → {message} (200)
POST /auth/resend-verification   → {message} (200)
```

## Quiz endpoints

```
POST /quiz/start                 → {session_id, question} 🔒
POST /quiz/answer                → {correct, explanation_es, explanation_en, ...} 🔒
POST /quiz/end                   → {total, correct, xp_earned} 🔒
```

## Progress endpoints

```
GET  /progress/dashboard         → overall stats 🔒
GET  /progress/skills?track_id=  → skill mastery list 🔒
GET  /progress/curriculum?track_id= → module/skill tree with BKT gates 🔒
GET  /progress/predictions?track_id= → DKT probability per skill 🔒
```

## Placement endpoints

```
POST /placement/start            → {session_id, question} 🔒
POST /placement/{session_id}/answer → next question or {finished, result} 🔒
GET  /placement/{session_id}/result → placement result 🔒
```

## Duel endpoints

```
POST /duels/challenge            → {duel_id, questions[]} 🔒
GET  /duels/my                   → list of my duels 🔒
POST /duels/{id}/answer          → {answered, completed} 🔒
GET  /duels/{id}/result          → {status, winner_id, scores} 🔒
```

## Tutor endpoint

```
POST /tutor/explain              → {explanation, provider, grounded, context_used} 🔒
  Body: {question_id, conversation_history?: [...]}
```

## Exam endpoints

Three kinds of sitting share one table and one clock. They differ in how they
are blueprinted and in what passing earns.

```
POST /exams/mock/start                      → certification mock (10.3), body {track_id}
POST /exams/mock/{attempt_id}/submit        → per-domain report, no pass/fail
GET  /exams/mock/{attempt_id}               → rereads a graded attempt

GET  /exams/track/{track_id}/blueprint      → questions, minutes, pass mark (before committing)
POST /exams/track/{track_id}/start          → course final exam (17.2)
POST /exams/module/{module_id}/test-out/start → module test-out (17.2)
POST /exams/track/{attempt_id}/submit       → per-skill report + verdict + certificate

GET  /exams/certificates/{code}             → PUBLIC, no auth
```

| Endpoint | Gotcha |
|---|---|
| `POST /exams/track/{...}/submit` | The path parameter is the **attempt id**, not the track id — you submit a *sitting*, and a track can be sat more than once. Starting takes a track id; submitting takes an attempt id |
| `POST /exams/track/{track_id}/start` | 400 on a certification track. Those have a published blueprint and go to `/exams/mock/start`; routing them here would replace it with our invented one |
| `POST /exams/mock/{...}/submit` | Never reports a pass or a scaled score. AWS computes its 100–1000 scale from item statistics we do not have, so the report gives the raw percentage and says why it refuses to convert |
| Certification mock `pass_pct` | `null`, for the same reason. Only `track_final` and `test_out` carry a pass mark |
| Late submission | Still graded — the work was done — but `status` becomes `expired` and it earns **no** certificate |
| Test-out mastery | A passed, on-time test-out feeds every answer through the same BKT/Elo/FSRS update a quiz answer gets, and returns `mastery_updated` (skill id → new mastery). It never grants mastery wholesale. A **failed** test-out changes nothing |
| `GET /exams/certificates/{code}` | **Unauthenticated on purpose**: whoever verifies a certificate has no account here. The 128-bit code is the only key, so certificates are not enumerable. A revoked certificate returns 200 with `revoked: true` — a 404 cannot be told apart from a code that never existed |
| Certificate uniqueness | One per (user, track), enforced by a unique index. Re-sitting a track you already passed returns the same code, so a shared URL never goes dead |

## Glossary endpoints

```
GET  /glossary/track/{track_id}  → [{term_es, term_en, definition_es, definition_en}]
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
