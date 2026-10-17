# App Store Review Guidelines — Whetzy Compliance Checklist
> Evaluated against Apple App Store Review Guidelines (current as of 2026-09)
> App: Whetzy · Bundle ID: app.whetzy · Category: Education

Legend: ✅ Compliant · ⚠️ Action needed · ❌ Blocker · N/A Not applicable

---

## 1. Safety

| # | Guideline | Status | Evidence / Notes |
|---|---|---|---|
| 1.1 | Objectionable Content | ✅ | Educational quiz app; no offensive material; content is AI-generated and QA-reviewed |
| 1.1.1 | Realistic portrayals of harm | ✅ | No violence, weapons, drug content |
| 1.2 | User Generated Content | ⚠️ | Las preguntas son admin-curadas (sin UGC), pero `username`/`display_name` son texto libre elegido por el usuario y **sí** son visibles para otro usuario: `duels.py` los usa para retar por `username` y en la notificación push del reto («X te retó a un duelo»); las ligas también exponen `display_name`. Confirmado en vivo (2026-09-30) que no existe filtro de palabras, ni reportar, ni bloquear usuario — `admin.py` no tiene nada de esto. Fila nueva 41.x (sin código todavía; sustituido el 2026-10-02 por 395d20f: filtro de nombres y reportar/bloquear en el backend, sin UI) |
| 1.2.1 | UGC moderation | ❌ | Filtro de nombres en `username`/`display_name` y endpoints `POST /moderation/report` y `POST /moderation/block` en el backend (395d20f, 2026-10-02), pero sin UI que los llame. Apple exige al menos uno de: filtrar contenido objetable, mecanismo de reporte, capacidad de bloquear, información de contacto publicada — hoy no hay ninguno |
| 1.3 | Kids Category | ✅ | App not targeting under-13; not submitted to Kids category; no COPPA obligation |
| 1.4 | Physical Harm | N/A | No health/medical advice beyond quiz content |
| 1.4.1 | Medical / Dangerous content | N/A | — |
| 1.5 | Developer Information | ⚠️ | App Store Connect must list valid support URL (whetzy.com), support email, and privacy policy URL |
| 1.6 | Data Security | ✅ | HTTPS everywhere; JWT auth; timing-safe login; ASVS L2 audit passed (7.1 DONE) |

---

## 2. Performance

| # | Guideline | Status | Evidence / Notes |
|---|---|---|---|
| 2.1 | App Completeness | ✅ | All features described in listing work; no stubs in production paths |
| 2.2 | Beta Testing | N/A | Not using TestFlight before final submission |
| 2.3.1 | Accurate Metadata — Screenshots | ⚠️ | Screenshots must show actual app UI, not mockups (task 9.3 pending) |
| 2.3.2 | Accurate Metadata — Description | ⚠️ | App description must match actual features; no mention of features not yet live |
| 2.3.3 | Accurate Metadata — Rating | ✅ | 4+ (no mature content) |
| 2.3.4 | Previews | ⚠️ | Optional but recommended; must use device recording (task 9.3) |
| 2.3.7 | Localized metadata | ⚠️ | App is bilingual (ES/EN); App Store listing should have both EN and ES localizations |
| 2.4 | Hardware Compatibility | ✅ | No hardware peripherals used |
| 2.4.1 | Location services | N/A | Not used |
| 2.5.2 | Código ejecutado en la app | ✅ | Whetzy cae en la excepción explícita de Apple para apps educativas que enseñan/prueban código ejecutable, con una condición: «the source code provided by the app [must be] completely viewable and editable by the user». Confirmado en vivo (2026-09-30): el editor es Monaco (`MonacoCodeEditor.tsx`, `QuizScreen.tsx`, `ProjectScreen.tsx`, `PlaygroundScreen.tsx`) — el alumno ve y edita el código real. Pyodide y sql.js van **empaquetados en el bundle** (`frontend/vite.config.ts`: `pyodideSelfHostPlugin` reescribe cualquier URL de CDN y sirve los ficheros desde `/pyodide/`; `useSqlRuntime.ts` sirve sql.js desde `/sql-js/`), no se descargan de un CDN en tiempo de ejecución |
| 2.5.4 | Push notifications | ✅ | User-initiated via ProfileScreen toggle; not used for advertising |

---

## 3. Business

| # | Guideline | Status | Evidence / Notes |
|---|---|---|---|
| **3.1.1** | **In-App Purchase (IAP)** | **❌ BLOCKER** | Whetzy currently uses Paddle (web checkout) for subscriptions. Apple requires all digital goods and subscriptions that unlock features *within the app* to use StoreKit/IAP. **Paddle web checkout = App Store rejection.** Fix: implement RevenueCat IAP (task 17.14) before iOS submission. **2026-09-27:** backend half done — `POST /billing/revenuecat/webhook` (RevenueCat → entitlements, sandbox-only, `REVENUECAT_WEBHOOK_AUTHORIZATION` unset in prod) writes the same `subscription_tier`/`is_premium`/`subscription_expires_at` Stripe already gates on. Still blocking: no client-side purchase UI/SDK (StoreKit + `@revenuecat/purchases-capacitor` on Android) — nothing to trigger the webhook from a real device yet, and live keys are H.2/H.3 (owner). |
| 3.1.1.a | Reader app exception | ⚠️ | If Whetzy qualifies as a "reader app" (consuming previously purchased content), external payment link may be allowed via [StoreKit External Purchase](https://developer.apple.com/documentation/storekit/appstore/externalpurchaselinkconfiguration). Evaluate post-17.14. |
| 3.1.2 | Subscriptions | ❌ | Same as 3.1.1 — must use IAP for in-app subscription upsell |
| 3.1.3 | Loot Boxes | N/A | No loot boxes; XP/badges earned through gameplay, not purchased |
| 3.2.1 | Acceptable Business Models | ✅ | Freemium with subscription; no advertising; no data monetization |
| 3.2.2 | Other App Variations | N/A | — |

---

## 4. Design

| # | Guideline | Status | Evidence / Notes |
|---|---|---|---|
| 4.1 | Copycats | ✅ | Original app; distinctive Whetzy brand |
| 4.2 | Minimum Functionality | ✅ | Full-featured learning engine; not a website wrapper with no native value |
| 4.2.2 | Primarily web content | ⚠️ | Capacitor apps are hybrid; ensure the App Store description emphasizes native value (offline, push, deep links, safe areas). Do NOT describe the app as "a website." |
| 4.3 | Spam | N/A | — |
| 4.5.6 | Apple Pay | N/A | Not using Apple Pay currently |
| 4.7 | HTML5 Games / Bots | ✅ | Not primarily a game; educational app with native shell |
| 4.8 | Sign in with Apple | ❌ | GitHub + Google OAuth ya están en vivo (`backend/app/api/v1/endpoints/oauth.py`, sin flag; botones en `AuthScreen.tsx`), confirmado el 2026-09-30 — 19.1 está hecho. Con OAuth de terceros ya activo, 4.8 **exige** Sign in with Apple **ahora**, no «desde que exista 19.1». No compilar iOS con este login social sin 19.2 (HUMAN-BLOCKED, H.2: Services ID + clave `.p8`, ADR-13) |

---

## 5. Legal

| # | Guideline | Status | Evidence / Notes |
|---|---|---|---|
| 5.1 | Privacy | ✅ | Privacy policy at `https://whetzy.com/privacy` (LegalScreen DONE) |
| 5.1.1 | Privacy Policy | ✅ | Policy URL configured; must be entered in App Store Connect |
| 5.1.2.1 | Data collection & use | ✅ | Privacy policy lists all data types; see play-store-data-safety.md for inventory |
| 5.1.2.2 | App Tracking Transparency (ATT) | ✅ | Whetzy does NOT use IDFA or cross-app tracking → ATT prompt not required |
| 5.1.2.4 | Data minimization | ✅ | Only email + username + quiz performance collected |
| 5.1.2.5 | Age gates / minors | ✅ | Registration requires age confirmation ("I am 13 or older" / parental consent per jurisdiction); 19.11 DONE |
| 5.1.3 | Health and health research | N/A | No HealthKit |
| 5.1.5 | Location services | N/A | Not used |
| 5.2 | Intellectual Property | ⚠️ | All questions must have `source` field populated with citable reference (task P.8 criterion). Verify 100% source coverage before submission |
| 5.2.1 | IP ownership | ✅ | App code is proprietary; content uses cited sources |
| 5.3 | Gambling | N/A | — |
| 5.4 | VPN | N/A | — |
| 5.5 | Developer Code of Conduct | ✅ | — |

---

## 6. Summary — Blockers and Action Items

### ❌ Hard Blockers (will be rejected)

| ID | Issue | Fix |
|---|---|---|
| B1 | Paddle web checkout used for in-app subscription upsell (3.1.1) | Implement RevenueCat StoreKit IAP (task 17.14). Do not submit to App Store until 17.14 is DONE. |

### ⚠️ Required Before Submission

| ID | Issue | Fix |
|---|---|---|
| A1 | No actual screenshots (9.3 pending) | Complete task 9.3; capture on iPhone 15 Pro Max (6.7") and iPhone SE (4.7") |
| A2 | App Store Connect metadata not created | Create listing in App Store Connect; fill EN + ES localizations |
| ~~A3~~ | ~~Age gate / minors~~ | ✅ DONE (19.11) — age confirmation in registration |
| A4 | Source coverage for all questions | 100% of questions must have non-empty `source` field (se comprueba con `python scripts/check_question_bank.py`) |
| A5 | Privacy policy URL in App Store Connect | Enter `https://whetzy.com/privacy` in the ASC app record |
| A6 | Support URL and email in App Store Connect | Enter `https://whetzy.com` and support email |
| A7 | Sign in with Apple (4.8) once any other social login exists | Ship 19.2 together with (or before) 19.1 in the iOS build; requires H.2 |

### ✅ Already Compliant

- ASVS L2 security audit (7.1)
- Privacy policy and Terms of Service (9.4, P.4)
- GDPR data export and deletion (P.7, 9.4)
- Push notifications opt-in (user-initiated, P.13)
- No IDFA / ATT not required
- No social login *today* → SIWA not required *yet* (see A7: changes with 19.1)
- No loot boxes or gambling mechanics
- Accessibility WCAG 2.2 AA (9.2)
- Prefers-reduced-motion support (9.1)
- Dark mode (P.10)
- Safe areas (7.5)

---

## 7. iOS Capacitor Submission Checklist

When the human runs `npx cap add ios` on a Mac:

- [ ] Set `Bundle Identifier` = `app.whetzy` in Xcode → Signing & Capabilities
- [ ] Set `Version` = `1.0` and `Build` = `1` (or use fastlane)
- [ ] Upload app icon set (1024×1024 App Store icon, all required sizes — task 9.3)
- [ ] Enable Push Notifications capability in Xcode (Signing & Capabilities → + Push Notifications)
- [ ] Add `NSUserNotificationUsageDescription` to Info.plist: `"Whetzy sends you duel challenges and streak reminders."`
- [ ] Enable Associated Domains for App Links (`applinks:whetzy.com`)
- [ ] Archive → Validate → Upload to App Store Connect
- [ ] Set correct age rating (4+)
- [ ] Submit for review **only after** task 17.14 (RevenueCat IAP) is DONE
