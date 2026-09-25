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
| 1.2 | User Generated Content | ✅ | No public UGC; questions are admin-curated via content agent |
| 1.2.1 | UGC moderation | N/A | — |
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
| 2.5.4 | Push notifications | ✅ | User-initiated via ProfileScreen toggle; not used for advertising |

---

## 3. Business

| # | Guideline | Status | Evidence / Notes |
|---|---|---|---|
| **3.1.1** | **In-App Purchase (IAP)** | **❌ BLOCKER** | Whetzy currently uses Stripe (web checkout) for subscriptions. Apple requires all digital goods and subscriptions that unlock features *within the app* to use StoreKit/IAP. **Stripe web checkout = App Store rejection.** Fix: implement RevenueCat IAP (task 17.14) before iOS submission. |
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
| 4.8 | Sign in with Apple | ⚠️ | Today email/password only, so 4.8 does not apply **yet**. Serie 19 adds GitHub + Google OAuth (19.1); from that moment 4.8 **requires** Sign in with Apple (19.2, needs H.2 Services ID + `.p8` key). Do not ship 19.1 in the iOS build before 19.2 is live (ADR-13) |

---

## 5. Legal

| # | Guideline | Status | Evidence / Notes |
|---|---|---|---|
| 5.1 | Privacy | ✅ | Privacy policy at `https://whetzy.com/privacy` (LegalScreen DONE) |
| 5.1.1 | Privacy Policy | ✅ | Policy URL configured; must be entered in App Store Connect |
| 5.1.2.1 | Data collection & use | ✅ | Privacy policy lists all data types; see play-store-data-safety.md for inventory |
| 5.1.2.2 | App Tracking Transparency (ATT) | ✅ | Whetzy does NOT use IDFA or cross-app tracking → ATT prompt not required |
| 5.1.2.4 | Data minimization | ✅ | Only email + username + quiz performance collected |
| 5.1.2.5 | Age gates / minors | ⚠️ | App has no age gate on registration. If users under 13 may register, COPPA/GDPR-K compliance is needed. Recommended: add age confirmation step or set minimum age 13 in ToS (link shown on AuthScreen) |
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
| B1 | Stripe web checkout used for in-app subscription upsell (3.1.1) | Implement RevenueCat StoreKit IAP (task 17.14). Do not submit to App Store until 17.14 is DONE. |

### ⚠️ Required Before Submission

| ID | Issue | Fix |
|---|---|---|
| A1 | No actual screenshots (9.3 pending) | Complete task 9.3; capture on iPhone 15 Pro Max (6.7") and iPhone SE (4.7") |
| A2 | App Store Connect metadata not created | Create listing in App Store Connect; fill EN + ES localizations |
| A3 | Age gate / minors | Add minimum-age confirmation (e.g., "I am 13 or older") to AuthScreen registration |
| A4 | Source coverage for all questions | 100% of questions must have non-empty `source` field (monitor via `GET /api/v1/content/questions?source=null`) |
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
