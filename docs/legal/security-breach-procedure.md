> **BORRADOR — pendiente de revisión profesional (H.20).** Este documento no ha sido
> revisado por un abogado. No tiene validez legal hasta que el dueño lo apruebe.

---

# Security Breach Procedure / Procedimiento de Brecha de Seguridad — Whetzy

**Version:** September 2026

---

## 1. Scope

This procedure applies to any confirmed or suspected breach of personal data
processed by Whetzy, as defined in GDPR Art. 4(12): "a breach of security leading
to the accidental or unlawful destruction, loss, alteration, unauthorised disclosure
of, or access to, personal data."

## 2. Detection & Classification

### 2.1 Sources of Detection
- Automated monitoring alerts (rate limiting, anomaly detection)
- User reports via support@whetzy.com
- Third-party vulnerability disclosures
- Internal audit findings
- Sub-processor notifications

### 2.2 Severity Classification

| Severity | Criteria | Response Time |
|---|---|---|
| **Critical** | Confirmed unauthorized access to personal data affecting >100 users, or any exposure of credentials/payment data | Immediate (within 1 hour) |
| **High** | Confirmed unauthorized access affecting <100 users, or exposure of learning data without credentials | Within 4 hours |
| **Medium** | Suspected breach, no confirmed data exposure | Within 24 hours |
| **Low** | Policy violation with no data exposure | Within 72 hours |

## 3. Response Timeline (GDPR Art. 33-34)

### 3.1 Within 72 Hours of Discovery
- **Hour 0-1:** Incident commander assigned, breach contained
- **Hour 1-4:** Initial assessment — scope, affected data categories, affected users
- **Hour 4-24:** Root cause analysis, evidence preservation
- **Hour 24-72:** Supervisory authority notification (if required)

### 3.2 Supervisory Authority Notification (Art. 33)

Required unless the breach is "unlikely to result in a risk to the rights and
freedoms of natural persons." The notification must include:

1. Nature of the breach (categories and approximate number of data subjects/records)
2. Name and contact details of the DPO or other contact point
3. Likely consequences of the breach
4. Measures taken or proposed to address and mitigate the breach

### 3.3 Data Subject Notification (Art. 34)

Required when the breach is "likely to result in a high risk to the rights and
freedoms of natural persons." Must be communicated without undue delay and include:

1. Clear description of the breach in plain language
2. Name and contact details of the DPO
3. Likely consequences
4. Measures taken and recommended protective actions

## 4. Notification Template

### To Supervisory Authority

```
Subject: Personal Data Breach Notification — Whetzy

Date of discovery: [DATE]
Date of breach (if different): [DATE]

1. NATURE OF THE BREACH
   - Description: [DESCRIPTION]
   - Categories of data subjects: [registered users / paying users / all users]
   - Approximate number of data subjects: [NUMBER]
   - Categories of personal data: [email, name, learning data, etc.]
   - Approximate number of records: [NUMBER]

2. DATA PROTECTION OFFICER
   - Name: [DPO NAME — pending appointment H.20]
   - Email: support@whetzy.com

3. LIKELY CONSEQUENCES
   [DESCRIPTION OF POTENTIAL IMPACT]

4. MEASURES TAKEN
   - Containment: [ACTIONS]
   - Mitigation: [ACTIONS]
   - Prevention: [PLANNED IMPROVEMENTS]

Signed: [INCIDENT COMMANDER]
```

### To Affected Users

```
Subject: Important Security Notice — Whetzy

Dear [NAME],

We are writing to inform you of a security incident that may have affected
your Whetzy account.

WHAT HAPPENED: [PLAIN LANGUAGE DESCRIPTION]
WHEN: [DATE/TIMEFRAME]
WHAT DATA WAS AFFECTED: [CATEGORIES]

WHAT WE ARE DOING:
- [CONTAINMENT MEASURES]
- [REMEDIATION STEPS]

WHAT YOU SHOULD DO:
- Change your Whetzy password immediately
- [ADDITIONAL RECOMMENDATIONS]

If you have questions, contact us at support@whetzy.com

The Whetzy Team
```

## 5. Post-Incident

- **Within 7 days:** Complete incident report filed internally
- **Within 30 days:** Remediation plan implemented and verified
- **Quarterly:** Review of breach procedure effectiveness
- All incidents logged in an internal breach register (GDPR Art. 33.5)

---

## 6. DSAR (Data Subject Access Request) SLA

Whetzy processes Data Subject Access Requests per GDPR Art. 12-23.

### 6.1 Self-Service (Immediate)
- **Data export:** `GET /api/v1/export/data` — JSON download from Profile
- **Account deletion:** Settings > Delete Account — triggers 30-day grace period
- **CCPA opt-out:** `POST /api/v1/privacy/ccpa-opt-out` — immediate

### 6.2 Manual Requests (via support@whetzy.com)
- **Acknowledgment:** within 3 business days
- **Fulfillment:** within 30 calendar days (GDPR Art. 12.3)
- **Extension:** up to 60 additional days for complex requests, with notification
- **Identity verification:** required for all manual requests (email confirmation
  from the account's registered email address)

### 6.3 Request Types & Response

| Request Type | GDPR Article | SLA | Method |
|---|---|---|---|
| Access / copy | Art. 15 | 30 days | Self-service or manual |
| Rectification | Art. 16 | 30 days | Profile settings or manual |
| Erasure | Art. 17 | 30 days + 30-day grace | Settings > Delete Account |
| Restriction | Art. 18 | 30 days | Manual only |
| Portability | Art. 20 | 30 days | Self-service (JSON export) |
| Objection | Art. 21 | 30 days | Manual only |

### 6.4 Refusal Grounds
Requests may be refused only when:
- The request is manifestly unfounded or excessive (Art. 12.5)
- Legal obligations require data retention
- The request affects the rights of others

Refusals are documented with reasons and communicated to the data subject
with information about the right to lodge a complaint with a supervisory authority.
