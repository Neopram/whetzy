---
title: "Multi-Jurisdiction Privacy Compliance Matrix"
last_updated: "2026-09-19"
effective_date: "2026-10-01"
language: "en"
status: "DRAFT - Requires legal review"
version: "1.0.0"
---

# Multi-Jurisdiction Privacy Compliance Matrix

## Legal Disclaimer

**This is a DRAFT document for internal review only. It has NOT been reviewed or approved by legal counsel and should NOT be used in production or shared with users until formally approved.** Whetzy Inc. reserves all rights and is not liable for any use of this document without proper legal authorization.

---

## Overview

This matrix documents privacy law applicability to Whetzy based on user location and data processing activities. Current status: **0 paying customers** (DEV/MVP phase). Applicability assumes expansion to each jurisdiction; impact assessments are prospective.

**Key Assumption**: Users can register from anywhere; no geographic restrictions currently enforced.

---

## Compliance Matrix

| Jurisdiction | Law | Applies Now | Impact on Policy | Key Requirements | User Data Risk Level |
|---|---|---|---|---|---|
| **European Union** | GDPR (2016/679) | YES (if any EU user) | REQUIRED | Legal basis, privacy policy, consent, DPIA, DPA, breach notification (72h), subject rights, processor agreements | HIGH |
| **United Kingdom** | UK GDPR + DPA 2018 | YES (if any UK user) | ALIGNED WITH GDPR | Aligned with GDPR; UK-specific ICO guidance; no separate register | HIGH |
| **California, USA** | CCPA (2020) + CPRA (effective 2025) | YES (if any CA user) | REQUIRED | Consumer rights notice, opt-out mechanisms, right to delete/correct, metrics disclosure, 45-day request window | MEDIUM-HIGH |
| **United States (Other)** | CAN-SPAM Act (email) | CONDITIONAL | Marketing emails need: clear subject, physical address, unsubscribe link, honor opt-out within 10 days | MEDIUM |
| **Brazil** | LGPD (Lei 13.709/2018) | YES (if any BR user) | REQUIRED | Legal basis, consent, controller/processor agreements, user rights (access, correction, deletion), breach notification (70 days) | MEDIUM-HIGH |
| **Mexico** | LFPDPPP (2010) + amendments | YES (if any MX user) | REQUIRED | Privacy policy, consent (opt-in for sensitive data), data transfer restrictions, user rights, 5-year retention | MEDIUM |
| **Colombia** | Ley 1581/2012 + Decreto 1377/2013 | YES (if any CO user) | REQUIRED | Authorization (consent) mandatory, privacy policy, data quality, user rights, DPA, processor appointment | MEDIUM |
| **Argentina** | Ley 25.326 (PDPA) + amendments | YES (if any AR user) | REQUIRED | Consent (explicit for sensitive), privacy notice, HABEAS DATA rights, no transfer without consent, 1-year retention default | MEDIUM |
| **Chile** | Ley 19.628 + Ley 21.719 (2022) | YES (if any CL user) | REQUIRED | Consent, privacy policy, data accuracy, user rights, transfers restricted, 6-month retention maximum (unless consent) | MEDIUM |
| **Peru** | Ley 29.733 + amendments | YES (if any PE user) | REQUIRED | Authorization (consent), privacy policy, registry disclosure, data accuracy, user rights, AEPD authority | MEDIUM |
| **USA (COPPA)** | Children's Online Privacy (13+) | CONDITIONAL | If targeting <13 years: parental consent, verifiable consent, limited data collection, no behavioral targeting | CRITICAL if violated |
| **Canada** | PIPEDA (federal) + provincial laws | CONDITIONAL | If CA user: consent, notice, accuracy, user rights, 30-day requests, no secondary use without consent | MEDIUM |

---

## Conclusion

Whetzy currently has 0 paying customers. Phase 1 compliance must complete before production launch.

**Status**: DRAFT for internal review
**Generated**: 2026-09-19
