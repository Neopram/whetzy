# Legal Documents

This directory contains DRAFT legal documents for the Whetzy learning platform.

---

## WARNING - DRAFT DOCUMENTS

These are DRAFT versions for internal review only. NOT reviewed by legal counsel. DO NOT use in production.

---

## Document Index

### 1. Privacy Policy
Data privacy and protection policy.
- [privacy-policy.en.md](./privacy-policy.en.md) - English
- [privacy-policy.es.md](./privacy-policy.es.md) - Spanish

Covers: Data collection, use, retention, user rights (GDPR, CCPA), processors, security, cookies, international transfers.

### 2. Terms of Service
Usage terms, licensing, payment, and dispute resolution.
- [terms-of-service.en.md](./terms-of-service.en.md) - English
- [terms-of-service.es.md](./terms-of-service.es.md) - Spanish

Covers: License (CC BY-NC-ND), acceptable use, account termination, payment (non-refundable), liability disclaimer.

### 3. Cookie Policy
Cookie usage, consent, and user control.
- [cookie-policy.en.md](./cookie-policy.en.md) - English
- [cookie-policy.es.md](./cookie-policy.es.md) - Spanish

Covers: Cookie types (essential, analytics), attributes, consent mechanisms, disable instructions, DNT.

### 4. IP Disclaimers
Intellectual property rights and copyright.
- [ip-disclaimers.en.md](./ip-disclaimers.en.md) - English
- [ip-disclaimers.es.md](./ip-disclaimers.es.md) - Spanish

Covers: Trademarks, content ownership, CC BY-NC-ND license, DMCA procedures, links, screenshots.

### 5. GDPR Data Processing Addendum (DPA)
GDPR compliance for EU/UK users.
- [dpa.en.md](./dpa.en.md) - English
- [dpa.es.md](./dpa.es.md) - Spanish

Covers: Data controller role, subject rights, sub-processors, security, breach response, retention schedules.

---

## Key Information

### Data Collected
- User Data: Name, email, profile, phone, date of birth (optional)
- Learning Data: Progress, quiz results, courses, study history
- Device Data: OS, browser, device fingerprints, user agent
- Network Data: IP address, ISP, connection type, location (approximate)
- Analytics: Pages visited, features used, time spent
- Payment: Transaction history (NOT card details - third-party processors)

### Data Retention
- Account Data: Active + 30 days soft-delete
- Learning Data: Duration of account
- Audit Logs: 90 days
- Device Fingerprints: 30 days
- Analytics: 30 days individual, indefinite aggregated
- Payment Records: 7 years (tax)
- Support Tickets: 2 years

### Payment Processors
- Stripe (USA) — **test mode only today; no live charges.** The live account is H.4.

> Paddle, Lemon Squeezy and RevenueCat were listed here by commit `5f7bd7b`.
> None of them exists in the code (`backend/app/core/config.py` declares Stripe only),
> and the payment rail is still an open owner decision (H.19, now gated by H.29).

### Data Processors
- Groq (USA) — tutor inference, model `qwen/qwen3.8-27b`
- Railway (USA/EU) — hosting and PostgreSQL
- Cloudflare (USA/EU) — CDN and Pages
- Email provider — SMTP or Resend, per `EMAIL_PROVIDER`
- Sentry — error tracking, **disabled by default** (`SENTRY_DSN` empty)

> Google Analytics was listed here by commit `5f7bd7b`. It is **not used**: red line 5
> forbids third-party trackers without explicit consent, and
> `frontend/scripts/check-no-third-party.mjs` proves none ships in `dist/`.

### User Rights (GDPR)
- Right to Access
- Right to Rectification
- Right to Erasure (right to be forgotten)
- Right to Restrict Processing
- Right to Data Portability
- Right to Object
- Right to Withdraw Consent

Exercise Rights: Email legal@whetzy.com

### Dispute Resolution
- Informal: support@whetzy.com (30 days)
- Formal: legal@whetzy.com
- Governing Law: [Jurisdiction - To Update]

---

## Implementation Checklist

Before production use:

- [ ] Legal review by qualified attorney
- [ ] Update jurisdictional placeholders
- [ ] Update company address
- [ ] Update contact emails and hours
- [ ] Appoint Data Protection Officer
- [ ] Verify data collection matches backend code
- [ ] Verify payment processors list
- [ ] Update sub-processor list (DPA Section 4)
- [ ] Add version checksums
- [ ] Set effective date
- [ ] Prepare user notification
- [ ] Set up legal@whetzy.com monitoring
- [ ] Set up DPIA process
- [ ] Train staff on data subject rights
- [ ] Implement cookie consent banner
- [ ] Set up breach notification procedures
- [ ] Prepare DMCA takedown process

---

## Contacts

Legal & Data Protection: legal@whetzy.com
Support: support@whetzy.com

---

## Document Versions

All documents: Version 1.0.0 (DRAFT) as of 2026-09-19
All documents marked as DRAFT pending legal review.

---

## Compliance Frameworks

- GDPR (EU data protection)
- CCPA (California privacy)
- DMCA (Copyright protection)
- EU Copyright Directive 2019/790
- Cookie and tracking regulations

---

## Next Steps

1. Legal review
2. Update placeholders
3. Establish contact infrastructure
4. User testing of consent/export/deletion flows
5. Website integration
6. Staff training
7. Annual review and updates

---

Status: DRAFT for internal review only
Generated: 2026-09-19
Distribution: Legal review team only

DO NOT DISTRIBUTE or use in production without authorization.
