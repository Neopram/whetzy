# Execution Plan — Series 25-29 (Full Go 2026-09-19)

**Status:** ALL GATES OPEN ✅
**Start Date:** 2026-09-20 (tomorrow)
**Timeline:** 4 weeks (Sep 20 - Oct 17)
**Authority:** User decision H.29 + H.20 + H.10 CONFIRMED

---

## Week 1: Foundation (Sep 20-26)

### Serie 25: Security Tracks (25.1-25.5)
- **25.1:** Landing cards marketplace (Haiku)
- **25.2-25.4:** Content creation Haiku (paralelo, 3 tracks × 400 Q each)
  - Track 13: Ciberseguridad (NIST + OWASP)
  - Track 24: Pentest (WSTG + ATT&CK)
  - Track 25: Cloud Sec (CSF + ASVS)
- **25.5:** QA + verificación (Sonnet)

### Serie 26: ES Distribution (26.0-26.3)
- **26.0:** Finalize plan + approval (User)
- **26.1-26.3:** Video rendering (User/Contractor)
  - Producto 2min ES (from 24.13)
  - Motor 5min ES (from 24.13)
  - Short 60s ES (from 24.13)

### Serie 28: Marketplace (28.1-28.3)
- **28.1-28.3:** Backend routes implementation + Paddle webhook setup (Agent)
  - POST /instructor/courses (course upload)
  - GET /instructor/analytics (dashboard)
  - Paddle webhook handlers (subscription.created, payout.completed)

### Serie 29: Economy (29.0-29.2)
- **29.0:** Confirm rules (already done 29-PLANNING.md)
- **29.1:** Credit ledger backend (Agent)
  - credit_transactions table (immutable log)
  - credit_balance (denormalized)
  - referral_links (K-factor)
- **29.2:** Wallet UI (Agent)
  - CreditWallet component (4 tabs)
  - Bilingual ES/EN

---

## Week 2: Integration (Sep 27 - Oct 3)

### Serie 25: Content + QA
- **25.5-25.10:** Autoría paralelo Haiku (1.200 Q × 3 tracks)
- Tests: check_question_bank.py PASS
- Verificador adversario (protocol §7)

### Serie 26: Upload + Analytics
- **26.4-26.6:** Publish on channels
  - YouTube ES (analytics tracking)
  - Dev.to articles (2 posts)
  - LinkedIn (5 posts)
- **26.7:** Measure cohort D1/D7 retention

### Serie 28: Payment Integration
- **28.4-28.6:** Instructor split logic
  - calculate_instructor_payout() (70/30)
  - Price cents in courses
  - Subscription revenue mapping
- **28.7:** Scheduled payouts
  - Job: run_payouts() (15th of month)
  - Minimum €50 payout

### Serie 29: Canje + Gamificación
- **29.3:** Redemption workflow
  - POST /economy/redeem/{type}
  - Créditos → Pro subscription
  - Créditos → Featured certificate
- **29.6:** Referral attribution
  - POST /referrals/accept/{code}
  - K-factor tracking

---

## Week 3: Optimization (Oct 4-10)

### Serie 25: Final Polish
- **25.6-25.14:** Remaining certifications + animations (Manim ~50)
- E2E testing (Playwright)

### Serie 26: Scale ES
- Measure metrics: views, conversions, D1 retention
- Email campaign (newsletter ES if exists)
- Community mentions (Reddit, Discord, X)

### Serie 28: Live Payouts
- **H.29 decision → Paddle/Stripe live activation**
- Test payout flow (€1 sandbox)
- First real payout to test instructor

### Serie 29: Gamification Integration
- **29.8:** Racha × créditos
  - D7 racha → +5 créditos
  - D30 racha → +25 créditos
  - D100 racha → +100 créditos
- **29.10:** Open Badges 3.0 (opcional H.27)
  - JSON-LD + QR
  - Verification endpoint
  - cNFT (if H.27 decided)

---

## Week 4: Production (Oct 11-17)

### Series 25-29: Final Verification
- All tests GREEN (pytest, vitest, e2e)
- CI-LOCAL: verify_ci_local.ps1 exit 0
- check_question_bank.py PASS
- check_docs.py PASS
- check_i18n_parity.py PASS (25 lang keys)

### Legal (H.20)
- Abogado review FINAL
- ToS/Privacy published (no BORRADOR)
- Créditos cláusulas + instructor tax warning

### Production Deployment (H.SEED)
- Database migrations (alembic upgrade head)
- content_loader run
- Paddle webhook production activation
- First users → Series 25-29 live

---

## Blockers & Dependencies

| Blocker | Gate | Resolution |
|---------|------|-----------|
| Paddle setup | H.29 | ~3 days (vendor ID + API key) |
| AFM registration | 21.1 | User action (1-2 days) |
| Video rendering | 26.1-26.3 | User/Contractor (~5 days) |
| Abogado review | H.20 | Lawyer task (1-2 weeks) |
| CI debug | 20.7 | Agente (1-2 days) |
| Admin endpoints | 22.1 | Agente (2-3 days) |

---

## Success Criteria

**Series 25:** 1.200 Q per track × 3, tests PASS, ≥15% executable
**Series 26:** 500+ views YouTube, 40%+ D1 retention, 150+ new users
**Series 28:** Instructor signup → course upload → enrollment → payout (sandbox)
**Series 29:** Credit ledger live, wallet UI functional, referral working (K-factor ≥1.1)
**Overall:** All 5 series TODO → 100% DONE or PARTIAL (verified by adversary)

---

## Command Chain (Agent Parallel)

```bash
# Week 1 - Start all 4 series in parallel
Agent(Serie 25: 25.1-25.5 content scaffolding)
Agent(Serie 26: 26.0-26.3 planning + rendering prep)
Agent(Serie 28: 28.1-28.7 payment integration)
Agent(Serie 29: 29.1-29.3 ledger + wallet)

# Week 2 - Full execution
Agent(Serie 25: autoría Haiku 1.200 Q)
Agent(Serie 26: upload + analytics)
Agent(Serie 28: instructor split logic)
Agent(Serie 29: canje + gamificación)

# Week 3-4 - Verification + production
Agent(Verificador adversario: protocol §7)
Agent(Final CI: verify_ci_local.ps1)
Agent(Legal review: H.20)
Agent(Deployment: H.SEED)
```

---

**EXECUTION AUTHORIZED ✅**
**Status: READY FOR AGENTS**
**Next Action: Launch Series 25-29 parallel agents**

