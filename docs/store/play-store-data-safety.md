# Play Store — Data Safety Declaration & Target API Level
> Whetzy · app.whetzy · Last updated: 2026-10-03 (§§1-7 payment/Sentry/Groq corrections per [S4]
> legal review on #93; §1 target API level content from 2026-09-08, task 9.6, unchanged)

## 1. Target API Level ✅

| Field | Value | Requirement |
|---|---|---|
| `compileSdkVersion` | **36** (Android 16) | — |
| `targetSdkVersion` | **36** | New apps and updates must target API 36 since **2026-08-31** (Google policy, extension to 2026-11-01 available); antes decía 35, un mes por detrás del plazo |
| `minSdkVersion` | 23 (Android 6.0) | Covers ~99 % of active devices |

Source: `frontend/android/variables.gradle`. Verificado en vivo el 2026-09-30 contra
`support.google.com/googleplay/android-developer/answer/11926878`, y verificado con una
compilación real (`./gradlew assembleDebug`, AGP 8.7.2, SDK 36 instalado ad-hoc para la
prueba): `BUILD SUCCESSFUL`, APK de 14,5 MB generado. No se pudo probar `bundleRelease`
(necesita el keystore de firma, H-bloqueado).

---

## 2. Data Safety Form — Answers

### 2.1 Does your app collect or share any of the required user data types?
**Yes.**

### 2.2 Is all of the data collected by your app encrypted in transit?
**Yes** — all traffic goes to `https://api-production-9751.up.railway.app` (TLS).

### 2.3 Do you provide a way for users to request that their data is deleted?
**Yes** — `DELETE /api/v1/auth/me/account` endpoint (bajo `/auth`, no `/me` a secas); link in ProfileScreen → `/delete-account`.

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
| Purchase history | ✅ (subscription tier/status) | ✅ RevenueCat / Google Play Billing | Entitlement gating |

> Note: on Android, purchases go through Google Play Billing via RevenueCat (`android/listing.md`
> §IAP) — Stripe exists as a web-checkout fallback rail in the backend (`PaymentRail.STRIPE`,
> not available in every market) but is never used by the Android app itself; raw card/payment
> data for Android purchases is handled exclusively by Google Play Billing and never transmitted
> to Whetzy servers.

### App activity

| Type | Collected | Shared | Purpose |
|---|---|---|---|
| App interactions | ✅ (quiz sessions, answers, accuracy, streaks, XP, level, track selection) | ❌ | Learning engine, progress tracking, gamification |
| In-app search history | ❌ | — | — |

### App info and performance

| Type | Collected | Shared | Purpose |
|---|---|---|---|
| Crash logs | ✅ (active in production since 2026-09-26) | ✅ Sentry | Debugging |
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
| **RevenueCat / Google Play Billing** | Subscription status, billing timestamps | Payment processing | revenuecat.com/privacy |
| **Groq** | Question text and the user's own question to the AI tutor (no name/email) | AI content generation / QA, and live tutor explanations (`/tutor`, Pro tier and up) | groq.com/privacy |
| **Sentry** | Anonymized crash logs | Error monitoring | sentry.io/privacy |
| **VAPID / Browser Push** | Push endpoint URL | Notification routing via user's own browser push service | — |

> Groq receives the text of questions being generated or reviewed, and — separately — the text
> of a live tutor question when a Pro-tier-or-above user asks the in-app AI tutor
> (`app/api/v1/endpoints/tutor.py`, `app/services/ai/tutor.py`) — never any user's name, email,
> or account data either way.

---

## 5. Data Handling & Retention

| Topic | Detail |
|---|---|
| Encryption in transit | TLS (HTTPS) for all API calls |
| Encryption at rest | Postgres managed by Railway (Railway encrypts volume at rest) |
| Data retention | Auth tokens expire; push subscriptions deleted on user unsubscribe or 410 Gone; user data deleted on account deletion |
| Data portability | `GET /api/v1/export/data` → JSON download (GDPR Art. 20) |
| Account deletion | `DELETE /api/v1/auth/me/account`; all user rows cascade-deleted |

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
| Data types: Financial info → Purchase history | Collected · Shared with RevenueCat/Google Play Billing · Analytics, account management · Required · Handled by Google Play Billing |
| Data types: App activity → App interactions | Collected · Not shared · Analytics, app functionality · Required · Not user-accessible directly |
| Data types: App info → Crash logs | Collected · Shared with Sentry · Analytics · Optional · Handled by Sentry |
| Data types: Device IDs → Other | Push endpoint collected · Not shared · App functionality (notifications) · Optional |
| Is all data encrypted in transit? | **Yes** |
| Can users request deletion? | **Yes** |

---

## 8. Action Items Before Submission

- [x] Sentry is **active** in production (confirmed `docs/legal/README.md` §"Procesadores verificados", 2026-10-01) — already listed above, no DPA action pending here
- [ ] If FCM push notifications are added (replacing Web Push), declare `POST_NOTIFICATIONS` permission
- [ ] Verify Play Console → Store listing → "Privacy policy URL" points to `https://whetzy.com/privacy`
- [x] The AI tutor (`/tutor`, Pro tier+) already sends user question text to Groq in
      production — listed above as its own row, separate from content generation/QA
