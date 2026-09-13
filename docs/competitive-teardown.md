# Whetzy — Competitive Teardown
*Prepared 2026-09-08 · Autonomous session ah*

## Scope

Head-to-head analysis of Whetzy against the three platforms most likely to appear in a user's mental shortlist: **Duolingo**, **Brilliant**, and **DataCamp**.  
Ratings: ✅ Strong · ⚠️ Gap · ❌ Missing

---

## 1. Feature Matrix

| Dimension | Whetzy | Duolingo | Brilliant | DataCamp |
|---|---|---|---|---|
| **Adaptive learning (BKT/DKT)** | ✅ BKT + DKT A/B | ⚠️ Rule-based streak | ⚠️ Light mastery gates | ⚠️ Skill tree |
| **Spaced repetition (FSRS)** | ✅ Full FSRS | ✅ Hearts/Super Duolingo | ❌ | ❌ |
| **Bilingual content** | ✅ ES/EN full | ✅ 40+ langs | ❌ EN only | ❌ EN only |
| **PWA / offline** | ✅ IDB queue | ✅ (limited) | ❌ | ❌ |
| **Native iOS/Android** | ⚠️ Capacitor shell ready | ✅ Native | ✅ Native | ✅ Native |
| **IAP / subscription** | ⚠️ Stripe web (blocked on iOS) | ✅ Premium | ✅ | ✅ |
| **AI tutor / explain** | ✅ Groq Qwen | ❌ | ⚠️ AI hints | ⚠️ AI assistant |
| **Gamification (leagues, duels)** | ✅ | ✅ Heavy | ❌ | ❌ |
| **Content quality pipeline** | ✅ QA agent + dupe detection | ❌ crowd | ❌ editorial | ✅ expert |
| **Progress analytics (admin)** | ✅ full dashboard | ❌ | ❌ | ✅ learner-level |
| **GDPR / data export** | ✅ | ✅ | ⚠️ | ⚠️ |
| **WCAG 2.2 AA** | ✅ (tested axe) | ⚠️ partial | ⚠️ | ⚠️ |
| **Exec / code sandbox** | ✅ Pyodide WASM | ❌ | ✅ (Brilliant cells) | ✅ (DataCamp IDE) |
| **Certification tracks** | ⚠️ Phase 10 roadmap | ❌ | ❌ | ✅ (career tracks) |
| **Marketing site** | ❌ (9.8 TODO) | ✅ | ✅ | ✅ |
| **Pricing / freemium wall** | ⚠️ Free + Plus/Pro Stripe | ✅ Hearts model | ✅ Free/Premium | ✅ Free/Teams |

---

## 2. Where Whetzy Leads

### 2.1 Adaptive Engine Depth
Whetzy is the only platform in this set that runs a **full three-model stack** (BKT mastery + FSRS scheduling + Elo item difficulty) with a live A/B experiment comparing BKT to a DKT LSTM. Duolingo's hearts/streak system is motivational, not diagnostic; Brilliant's mastery gates are binary; DataCamp uses a static skill tree. Whetzy's approach is closer to what research (Piech 2015, Settles & Meeder 2016) shows maximises long-term retention.

### 2.2 Bilingual-First Architecture
Full ES/EN content with i18n-capable React frontend. None of the competitors serve Spanish as a *source* language for technical content — they are EN-first with EN-only explanations. This is a defensible wedge for the Spanish-speaking professional market (LATAM + Spain ≈ 500 M people).

### 2.3 Content Pipeline Automation
The author agent + QA agent + duplicate detector pipeline can generate and validate questions at 10–100× human speed with traceable citations. Competitors rely on editorial teams (DataCamp) or crowdsourcing (Duolingo). This is a structural moat if the pipeline output quality stays high.

### 2.4 Pyodide Code Execution
In-browser sandboxed Python execution (Pyodide + SharedArrayBuffer + import-block) without a remote eval server. Brilliant has a similar feature but requires account sign-in and a subscription. Whetzy's sandbox is COOP/COEP hardened and has a 5-second interrupt — meeting ASVS L2.

---

## 3. Concrete Gaps and Actions

### GAP-1: No native IAP → iOS App Store blocker (HIGH)
**Duolingo / DataCamp / Brilliant**: All have native IAP on iOS.  
**Whetzy**: Stripe web checkout violates 3.1.1. App Store rejection is certain.  
**Action**: 7.6 RevenueCat IAP — required before any iOS submission. No workaround.  
**Owner**: Human (Apple Dev account + device).

### GAP-2: No marketing site → zero organic acquisition (HIGH)
**All competitors**: Full-featured landing page, pricing comparison, testimonials, blog.  
**Whetzy**: No landing page; `whetzy.com` serves the SPA directly to un-authenticated users.  
**Action**: 9.8 — one-page landing with value props, pricing table, CTA to signup. Can be a separate static route (`/landing`) or a full Cloudflare Pages site.  
**Effort**: 1–2 days frontend, 0 backend. Unblocked.

### GAP-3: Native shell unfinished → no App Store / Play Store presence (HIGH)
**Competitors**: Native experiences with platform-native gestures, deep link handling.  
**Whetzy**: Capacitor shell generated, Android icons patched, but no submission yet.  
**Action**: H.4 (Google Play internal test), H.5 (Apple TestFlight) — human-blocked on accounts.

### GAP-4: No certification tracks → DataCamp's biggest differentiator (MEDIUM)
**DataCamp**: Career tracks and certificates. Highly employability-focused.  
**Whetzy**: Phase 10 roadmap exists but not started.  
**Action**: 10.1–10.3. Starts after Phase 9 closes.

### GAP-5: AI tutor visibility low → Brilliant's explainer advantage (MEDIUM)
**Brilliant**: "Explain why" button is prominent on every question.  
**Whetzy**: `/tutor/explain` exists (Plus tier) but the quiz UX buries it.  
**Action**: Surface the "¿Por qué?" / "Why?" button inline in QuizScreen (no backend change needed). Low effort, high perceived value.

### GAP-6: No social proof or testimonials on landing (MEDIUM — follows GAP-2)
**Duolingo / DataCamp**: DAU metrics, celebrity endorsements, case studies.  
**Whetzy**: Zero. At launch, replace with quantified product claims: "X questions answered", "Y% average accuracy gain over 7 days", generated from the analytics dashboard.

### GAP-7: k6 load test not run against Railway prod (LOW)
Local 4-worker uvicorn ≠ Railway free tier (single dyno, cold-start ~3s).  
**Action**: Run `k6 run` against `https://api-production-9751.up.railway.app` once prod is warm. Adjust `P95_BUDGET_MS` threshold to 3000 for prod baseline.

---

## 4. Priority Matrix

| Gap | Impact | Effort | When |
|---|---|---|---|
| GAP-2: Marketing site | HIGH | LOW | Now (9.8) |
| GAP-5: AI tutor button | HIGH | LOW | Now (QuizScreen tweak) |
| GAP-1: IAP RevenueCat | CRITICAL | HIGH | After human unblocks Apple Dev |
| GAP-3: Store submission | CRITICAL | MEDIUM | After GAP-1 |
| GAP-4: Certs | MEDIUM | VERY HIGH | Phase 10 |
| GAP-6: Social proof | MEDIUM | LOW | After GAP-2 |
| GAP-7: Prod load test | LOW | LOW | Any time |

---

## 5. Strategic Summary

Whetzy's defensible position is **adaptive depth + bilingual content + automated pipeline** — none of the three competitors have all three simultaneously. The critical path to the market is:
1. **Close IAP blocker** (7.6) → enables iOS → enables App Store review.
2. **Marketing site** (9.8) → enables user acquisition before stores.
3. **Surface AI tutor inline** → differentiates on first-use experience.

DataCamp is the closest competitor on content quality but has no adaptive engine. Duolingo is the closest on gamification but has no professional/technical track. Brilliant has the code execution and interactive explanation but is EN-only and has no spaced repetition. Whetzy's gap is distribution (no app store presence, no marketing site) not product — close those two and the wedge is real.

---

## 6. Re-evaluación honesta — 2026-09-12

The 8 September teardown and the 11 September Launch Console (77/100) scored **code inventory against products in market**. The owner asked whether that was brutally realistic. It was not. This section replaces the earlier scoring; §1–§5 stay as the feature inventory they are.

### 6.1 What was inflated, and why

| Claim | What §1 said | What is true today | Honest score |
|---|---|---|---|
| Adaptive engine | Whetzy 95, Duolingo 40 | Duolingo *invented* half-life regression (Settles & Meeder 2016 — the paper cited in §2.1 in Whetzy's favour) and trains it on billions of responses. Whetzy's own eval (4.2): DKT AUC 0.24, BKT 0.33 on 3 validation sequences — **both below chance**. The stack exists; its efficacy has zero evidence | **35** (Duolingo 85) |
| Content quality | 80 vs DataCamp 90 | 1,253 MCQ / fill-blank items vs thousands of hours of video, notebooks and projects (DataCamp) or interactive visualisations per lesson (Brilliant). 100 % sourced is real and rare — but it is thin | **35** |
| AI tutor | 85, "grounded RAG" | ChromaDB + sentence-transformers were **removed from prod** (OOM on Railway free tier, session o). The prod tutor is Qwen-27B with the canonical explanation pasted in — no retrieval. `grounded=True` is not backed by a retrieved source. Khanmigo / DataCamp AI are years ahead | **45** |
| Code execution | 80 vs DataCamp 90 | 7 exec questions out of 1,253 (0.6 %). DataCamp *is* an IDE | **30** |
| Gamification | 75 | 5 leagues, 4 missions, 8 badges, duels — touched by **zero users**. No D1/D7 measured | **40** |
| Bilingual | 90 | Genuinely native ES+EN with sources. Real niche. Still 1,253 items | **80** |
| PWA / offline | 85 | Implemented and E2E-tested in Chromium; never verified on a real mid-range Android over 4G | **70** |
| WCAG | 90 | axe-core clean; no screen-reader pass (9.7 blocked) | **75** |
| Distribution | 25 | Zero users, zero store presence, backend **down** since ≤ 2026-09-11 | **0** |
| Pricing | "competitive" | $9.99 / $19.99 for an unknown MCQ app vs Duolingo Super at $6.99. Aspirational, not tested | — |

**Weighted honest score: Whetzy ≈ 30 / 100.** Duolingo ≈ 72, DataCamp ≈ 68, Brilliant ≈ 66, Codecademy ≈ 58 (their scores in the earlier table were also depressed to flatter the comparison).

### 6.2 What is genuinely true and defensible

- **Spanish-native technical content with canonical citations.** Nobody in the set does this. It is a real thesis for a ~500 M-speaker market — but it is a thesis, not a validated advantage, until users retain on it.
- **Engineering hygiene far above an indie baseline**: 451 tests, mypy/tsc strict, ASVS L2 audit, real GDPR export/delete, WCAG AA (axe), CI green, Alembic discipline, k6 load test. This is a **foundation**, not a moat — users do not see it.
- **Content pipeline (5.1–5.3) exists.** It is a capability; the bank is still 1,253.
- **Team of one + AI** against companies with hundreds of engineers and a decade of learner data. That asymmetry does not go away by writing it down.

### 6.3 What would make "Whetzy leads" a true sentence

Each row maps a gap to the ledger task whose acceptance criterion is the *evidence* that would move the score. None of these is DONE by existing; each is DONE by measuring.

| Gap | Evidence that closes it | Ledger | Score moves |
|---|---|---|---|
| Tutor not grounded in prod | BM25 retrieval in prod, self-retrieval ≥ 95 % top-3, `grounded` reflects a real hit | 11.1 | AI tutor 45 → 70 |
| Tutor invisible | Inline "¿Por qué?" on every feedback, Playwright-tested, ES/EN | 11.2 | AI tutor +10 |
| Engine has no evidence | DKT AUC ≥ 0.70 and > BKT on the public `synthetic-5` benchmark (Piech 2015) | 11.3 | Adaptive 35 → 60 |
| Exec questions 0.6 % | ≥ 15 % exec in tracks 01–03, every expected output verified by actually running CPython in CI | 11.4 | Code exec 30 → 60 |
| Bank at 1,253 | ≥ 1,500 sourced items, structural QA green | P.8 | Content 35 → 45 |
| Coverage is a guess | Measured ≥ 80 % with `--cov-fail-under` | 11.5 | (foundation) |
| No users | 30-person beta: D1 ≥ 40 %, D7 ≥ 20 %, mean `p_known` gain ≥ +0.20 per practised skill | 11.8 (H.10) | Adaptive +15, Gamification 40 → 60 |
| Backend down / unmeasured in prod | TTFQ < 60 s and p95 < 500 ms against `whetzy.com` | 11.6, 11.9 (H.1) | Distribution 0 → 15 |
| No organic acquisition | Lighthouse SEO ≥ 95, sitemap, hreflang | 11.7 | Distribution +10 |
| Not in stores | IAP + submission | 7.6, H.2–H.5 | Distribution +30 |

Realistic ceiling with all of the above done and measured: **≈ 60–65 / 100** — parity on a narrower, better-served niche, not dominance. "Superar con creces a toda la competencia" is not a claim this document can make; it is a target the ledger can earn.
