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
POST /quiz/skip                  → next question or session_done 🔒
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

## Glossary endpoints

```
GET  /glossary/track/{track_id}  → [{term_es, term_en, definition_es, definition_en}]
GET  /glossary/term/{term_id}    → GlossaryTerm
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
