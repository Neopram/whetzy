# Play Store — Data Safety Declaration & Target API Level
> Whetzy · app.whetzy · Last updated: 2026-09-08 (task 9.6)

## 1. Target API Level ✅

| Field | Value | Requirement |
|---|---|---|
| `compileSdkVersion` | 35 (Android 15) | — |
| `targetSdkVersion` | **35** | ≥ 34 required for new apps (Google policy Nov 2024) |
| `minSdkVersion` | 23 (Android 6.0) | Covers ~99 % of active devices |

Source: `frontend/android/variables.gradle`. **No change needed.**

---

## 2. Data Safety Form — Answers

### 2.1 Does your app collect or share any of the required user data types?
**Yes.**

### 2.2 Is all of the data collected by your app encrypted in transit?
**Yes** — all traffic goes to `https://api-production-9751.up.railway.app` (TLS).

### 2.3 Do you provide a way for users to request that their data is deleted?
**Yes** — `DELETE /api/v1/auth/me` endpoint; link in ProfileScreen → LegalScreen → `/delete-account`.

---

## 3. Data Types — Detail

### Personal info

| Type | Collected | Shared | Purpose | Required / Optional |
|---|---|---|---|---|
| Name | ✅ (username) | ❌ | Display, leaderboard | Required |
| Email address | ✅ | ❌ | Auth, transactional email (reset, verification, streak reminders) | Required |
| Password | hash only (never stored plaintext) | ❌ | Auth | Required |

### Financial info

| Type | Collected | Shared | Purpose |
|---|---|---|---|
| Purchase history | ✅ (subscription tier/status) | ✅ Stripe (payment processor) | Entitlement gating |

> Note: Raw card/payment data is handled exclusively by Stripe and never transmitted to Whetzy servers.

### App activity

| Type | Collected | Shared | Purpose |
|---|---|---|---|
| App interactions | ✅ (quiz sessions, answers, accuracy, streaks, XP, level, track selection) | ❌ | Learning engine, progress tracking, gamification |
| In-app search history | ❌ | — | — |

### App info and performance

| Type | Collected | Shared | Purpose |
|---|---|---|---|
| Crash logs | ✅ (optional, via Sentry if `SENTRY_DSN` is set) | ✅ Sentry (only if configured) | Debugging |
| Diagnostics | ❌ | — | — |

### Device or other IDs

| Type | Collected | Shared | Purpose |
|---|---|---|---|
| Push notification token (Web Push endpoint) | ✅ | ❌ (stored on Whetzy backend only) | Duel notifications, streak reminders |
| Advertising ID | ❌ | — | Not used |

### NOT collected

Location · Photos/videos · Audio · Contacts · Emails/text messages · Files/docs ·
Calendar events · Health data · Fitness data · Web browsing history · Other installed apps.

---

## 4. Sharing with Third Parties

| Third Party | Data shared | Purpose | Link |
|---|---|---|---|
| **Stripe** | Subscription status, billing timestamps | Payment processing | stripe.com/privacy |
| **Groq** | Question text (no PII) | AI content generation / QA (task 5.1, 5.2) | groq.com/privacy |
| **Sentry** (optional) | Anonymized crash logs | Error monitoring | sentry.io/privacy |
| **VAPID / Browser Push** | Push endpoint URL | Notification routing via user's own browser push service | — |

> Groq receives only the text of questions being generated or reviewed — never any user's identity, answers, or account data.

---

## 5. Data Handling & Retention

| Topic | Detail |
|---|---|
| Encryption in transit | TLS (HTTPS) for all API calls |
| Encryption at rest | Postgres managed by Railway (Railway encrypts volume at rest) |
| Data retention | Auth tokens expire; push subscriptions deleted on user unsubscribe or 410 Gone; user data deleted on account deletion |
| Data portability | `GET /api/v1/export/data` → JSON download (GDPR Art. 20) |
| Account deletion | `DELETE /api/v1/auth/me`; all user rows cascade-deleted |

---

## 6. Permissions in AndroidManifest.xml

| Permission | Declared | Reason |
|---|---|---|
| `INTERNET` | ✅ | Backend API calls |
| `POST_NOTIFICATIONS` | Not declared in manifest | Web Push uses browser/PWA path, not native FCM; add if implementing native FCM push |
| Location, Camera, Contacts, etc. | ❌ | Not used |

---

## 7. Play Console Form — Field-by-Field

> Use this table when filling the "Data safety" section in Play Console.

| Question | Answer |
|---|---|
| Does the app collect or share user data? | **Yes** |
| Data types: Personal info → Name | Collected · Not shared · Account management · Required · Handled by user |
| Data types: Personal info → Email | Collected · Not shared · Account management, App functionality · Required · Handled by user |
| Data types: Financial info → Purchase history | Collected · Shared with Stripe · Analytics, account management · Required · Handled by Stripe |
| Data types: App activity → App interactions | Collected · Not shared · Analytics, app functionality · Required · Not user-accessible directly |
| Data types: App info → Crash logs | Collected (if Sentry configured) · Shared with Sentry · Analytics · Optional · Handled by Sentry |
| Data types: Device IDs → Other | Push endpoint collected · Not shared · App functionality (notifications) · Optional |
| Is all data encrypted in transit? | **Yes** |
| Can users request deletion? | **Yes** |

---

## 8. Action Items Before Submission

- [ ] Confirm Sentry is **disabled** on prod or add Sentry to the third-party list with their DPA
- [ ] If FCM push notifications are added (replacing Web Push), declare `POST_NOTIFICATIONS` permission
- [ ] Verify Play Console → Store listing → "Privacy policy URL" points to `https://whetzy.com/privacy`
- [ ] If Groq processes any user input (e.g., future tutor chat sessions), add Groq to data sharing table with appropriate data type (User Content)
