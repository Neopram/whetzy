---
title: "GDPR Data Processing Addendum (DPA)"
last_updated: "2026-09-19"
effective_date: "2026-10-01"
language: "en"
status: "DRAFT — pending professional legal review (H.20)"
version: "1.0.0"
---

# GDPR Data Processing Addendum (DPA)

## Legal Disclaimer

**DRAFT — pending professional legal review (H.20).**

This is a DRAFT document for internal review only. NOT reviewed/approved by legal counsel.

---

## 1. Definitions

- **Data Controller**: the Service operator [LEGAL ENTITY PENDING — H.29] (determines purposes/means of processing)
- **Data Subject**: End user providing personal data
- **Personal Data**: Information relating to identified/identifiable person
- **Processing**: Any operation on personal data
- **GDPR**: EU Regulation 2016/679

---

## 2. Data Controller Responsibilities

### 2.1 Whetzy's Role

Whetzy acts as Data Controller for:
- User account data
- Learning progress and performance data
- Device and usage analytics
- Payment and billing information

### 2.2 Legal Basis for Processing

Whetzy processes under:
- Contract (account and learning data)
- Legitimate interest (analytics, fraud prevention)
- Legal obligation (payment/tax compliance)
- Consent (marketing emails)

### 2.3 Data Protection Obligations

Whetzy commits to:
- Process data only for specified purposes
- Collect only necessary data
- Keep data accurate and up-to-date
- Implement security measures
- Respect data subject rights
- Report breaches within 72 hours

---

## 3. Data Subject Rights

### 3.1 Right to Access

Request: Email legal@whetzy.com
Response: Within 30 days

### 3.2 Right to Rectification

Request: Update via dashboard or email legal@whetzy.com
Response: Within 30 days

### 3.3 Right to Erasure (Right to be Forgotten)

Grounds: Data unnecessary, withdrawal of consent, unlawful processing

Process:
1. Submit deletion request to legal@whetzy.com
2. Soft-delete: Immediate
3. Grace period: 30 days (recovery possible)
4. Hard-delete: After 30 days

Exceptions: Legal obligations, audit logs (90 days), anonymized data

### 3.4 Right to Restrict Processing

Request limits on data use. Whetzy marks as restricted.

### 3.5 Right to Data Portability

Request personal data in JSON/CSV format.
Process: Email legal@whetzy.com; export via API in 30 days

### 3.6 Right to Object

Object to marketing, processing, profiling.
Whetzy ceases within 30 days.

### 3.7 Right to Withdraw Consent

Withdraw from marketing: Unsubscribe link
Withdraw from analytics: Cookie preferences
Other: Email legal@whetzy.com

---

## 4. Sub-Processors

### 4.1 Approved Sub-Processors

- Railway: hosting and PostgreSQL database (EU)
- Cloudflare: CDN and Pages
- Groq: AI tutor inference (qwen/qwen3.8-27b model)
- Stripe: payments (currently test mode only, no live charges; the live account is pending — H.4)
- Email provider: SMTP or Resend, depending on the EMAIL_PROVIDER variable
- Sentry: error tracking (disabled; SENTRY_DSN empty by default)

### 4.2 Sub-Processor Changes

Changes notified 30 days in advance. Right to object within 30 days.

---

## 5. Data Security

### 5.1 Technical Measures

- HTTPS/TLS encryption in transit
- AES-256 encryption at rest
- Bcrypt/Argon2 password hashing
- Optional 2FA
- Security audits and penetration testing
- Intrusion detection systems

### 5.2 Organizational Measures

- Staff training on data protection
- Role-based access controls
- Confidentiality agreements
- Incident response plan
- Privacy by design and default

### 5.3 Breach Response

- Immediate investigation
- Notify the relevant supervisory authority within 72 hours
- Notify affected users if high risk
- Document breach and response
- Communicate with processors

---

## 6. Data Retention and Deletion

### 6.1 Retention Schedule

- Account profile: Active + 30 days
- Learning data: Active only
- Audit logs: 90 days
- Device fingerprints: 30 days
- Payment records: 7 years (tax obligation)
- Analytics: 30 days individual, indefinite aggregated
- Support tickets: 2 years

### 6.2 Deletion Process

1. Soft-delete: Immediate anonymization
2. Grace period: 30 days
3. Hard-delete: Permanent removal
4. Verification: Confirmation email
5. Documentation: Logged in audit trail

---

## 7. Data Protection Impact Assessment

Whetzy conducts DPIAs for:
- High-risk processing
- New technology introduction
- Changes to collection/use
- Large-scale processing

Assessments evaluate necessity, risks, and mitigations.

---

## 8. International Data Transfers

### 8.1 Legal Mechanism

Transfers from EU/UK rely on:
- Standard Contractual Clauses (SCCs)
- Data Processing Agreements
- Adequacy decisions (where applicable)

### 8.2 Schrems II Compliance

Following EU Court decision:
- Supplementary safeguards in place
- Technical measures to limit US government access
- Monitoring of US law changes
- Alternative storage options available

---

## 9. Changes to DPA

Material changes: 30-day notice via email
Non-material changes: Posted here
Continued use = acceptance

---

## 10. Dispute Resolution

### 10.1 Informal

Contact legal@whetzy.com; 30-day resolution period.

### 10.2 Formal

Lodge complaint with:
- EU Supervisory Authority
- UK ICO
- National Data Protection Authority

---

## 11. Governing Law

- GDPR Regulation 2016/679
- Data Protection Act 2018 (UK)
- [GOVERNING LAW PENDING — H.29]

---

## 12. Contact

- **Legal & Data Protection**: legal@whetzy.com
- **Support**: support@whetzy.com
- **DPO**: To be appointed
- **Address**: To be updated

---

Version: 1.0.0 (DRAFT)

DRAFT NOTICE: Not approved by legal counsel. Requires formal review before processing EU/UK personal data.
