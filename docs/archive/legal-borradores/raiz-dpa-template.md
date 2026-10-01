> **BORRADOR — pendiente de revisión profesional (H.20).** Este documento no ha sido
> revisado por un abogado. No tiene validez legal hasta que el dueño lo apruebe y lo
> publique.

---

# Data Processing Agreement (DPA) Template — Whetzy

**Version:** September 2026

This DPA template is used between Whetzy ("Controller" / "Data Exporter") and its
sub-processors ("Processor" / "Data Importer") to ensure GDPR-compliant data processing.

---

## 1. Definitions

- **Personal Data**: any information relating to an identified or identifiable natural
  person (GDPR Art. 4.1)
- **Processing**: any operation performed on Personal Data (GDPR Art. 4.2)
- **Controller**: Whetzy, which determines the purposes and means of Processing
- **Processor**: the sub-processor providing services to Whetzy
- **Data Subject**: the individual whose Personal Data is Processed
- **Sub-processor**: any third party engaged by Processor to Process Personal Data

## 2. Scope & Purpose

The Processor processes Personal Data on behalf of the Controller solely for the
purpose of providing the services described in the main service agreement between
the parties. The categories of data and data subjects are:

| Category | Data Subjects | Data Elements | Retention |
|---|---|---|---|
| Account data | Registered users | Email, display name, avatar, hashed password | While account is active + 30 days |
| Learning data | Registered users | Quiz responses, scores, mastery levels, FSRS/Elo/BKT parameters | While account is active + 30 days |
| Device data | All users | Device type, OS version, language, timezone | Session duration |
| Usage analytics | All users | Session duration, feature interactions (anonymized) | Indefinite (anonymized only) |
| Payment data | Paying users | Billing info (processed by Stripe — not stored by Whetzy) | Per Stripe retention policy |
| AI Tutor context | Pro/Pro Max users | Current question text sent to Groq | Not retained by Whetzy; Groq's retention per their DPA |

## 3. Obligations of the Processor

The Processor shall:

a) Process Personal Data only on documented instructions from the Controller, including
   with regard to transfers to a third country (GDPR Art. 28.3.a)

b) Ensure that persons authorized to process the Personal Data have committed themselves
   to confidentiality or are under an appropriate statutory obligation (Art. 28.3.b)

c) Take all measures required pursuant to Article 32 (security of processing), including
   but not limited to:
   - Encryption of data in transit (TLS 1.3 minimum) and at rest
   - Pseudonymization where feasible
   - Regular testing and assessment of security measures
   - Access controls limiting data access to authorized personnel

d) Not engage another processor without prior specific or general written authorization
   of the Controller. In the case of general written authorization, the Processor shall
   inform the Controller of any intended changes concerning the addition or replacement
   of sub-processors, giving the Controller the opportunity to object (Art. 28.2)

e) Assist the Controller in responding to data subject requests (access, rectification,
   erasure, restriction, portability, objection) within the timeframes required by
   applicable law (Art. 28.3.e)

f) Assist the Controller in ensuring compliance with obligations regarding security,
   breach notification, data protection impact assessments, and prior consultation
   (Art. 28.3.f, Arts. 32-36)

g) At the choice of the Controller, delete or return all Personal Data after the end
   of the provision of services, and delete existing copies unless EU or Member State
   law requires storage (Art. 28.3.g)

h) Make available to the Controller all information necessary to demonstrate compliance
   with the obligations laid down in Article 28, and allow for and contribute to audits,
   including inspections, conducted by the Controller or another auditor mandated by
   the Controller (Art. 28.3.h)

## 4. Data Breach Notification

The Processor shall notify the Controller without undue delay after becoming aware of
a personal data breach. The notification shall include:

- The nature of the breach, including the categories and approximate number of data
  subjects and records concerned
- The name and contact details of the data protection officer or other point of contact
- The likely consequences of the breach
- Measures taken or proposed to address the breach and mitigate its effects

The Controller is responsible for notifying the supervisory authority within 72 hours
(Art. 33) and affected data subjects without undue delay where required (Art. 34).

## 5. International Transfers

Where the Processor transfers Personal Data outside the EEA, it shall ensure an adequate
level of protection through one of the following mechanisms:

- European Commission adequacy decisions (Art. 45)
- Standard Contractual Clauses (SCCs) as approved by the European Commission (Art. 46.2.c)
- Binding Corporate Rules (Art. 47)
- Approved certification mechanisms (Art. 42)

Transfer impact assessments shall be conducted where required.

## 6. Current Sub-processors

The Controller has authorized the following sub-processors:

| Sub-processor | Service | Data Processed | Location |
|---|---|---|---|
| Railway | Backend hosting, database | All user data | US/EU |
| Cloudflare | CDN, frontend hosting | Request metadata | Global (edge) |
| Stripe | Payment processing | Billing data only | US/EU |
| Groq | LLM inference (AI Tutor) | Question context only (no PII) | US |

Changes to the sub-processor list will be communicated to users via an update to
the Privacy Policy with at least 30 days' notice.

## 7. Duration & Termination

This DPA remains in effect for the duration of the main service agreement. Upon
termination, the Processor shall comply with Section 3(g) regarding deletion or
return of Personal Data.

## 8. Liability

Each party's liability under this DPA is subject to the limitations set out in the
main service agreement. Nothing in this DPA limits a party's liability for breaches
of its obligations under applicable data protection law.

## 9. Governing Law

This DPA is governed by the same law that governs the main service agreement. For
disputes related to data protection, the competent supervisory authority is determined
by the data subject's habitual residence or place of work (GDPR Art. 77).

---

## Annex: Technical & Organizational Measures (TOMs)

Whetzy implements the following measures to protect Personal Data:

**Access Control**
- Role-based access control (RBAC) with owner-only admin access
- JWT tokens with short-lived access (30 min) and long-lived refresh (30 days)
- bcrypt-hashed passwords (never stored in plain text)
- Password reset and email verification tokens stored as SHA-256 hash only

**Encryption**
- TLS 1.3 for all data in transit
- Database encryption at rest (managed by Railway)
- No sensitive data in client-side storage

**Data Minimization**
- AI Tutor sends only question context to Groq (no PII)
- Analytics data anonymized before aggregation
- Usage data collected only for service improvement

**Incident Response**
- Breach notification procedure within 72 hours
- Security incident template maintained at `legal/`
- Audit trail of administrative actions

**Data Subject Rights**
- Self-service data export: `GET /api/v1/export/data`
- Self-service account deletion: Settings > Delete Account
- CCPA opt-out endpoint: `POST /api/v1/privacy/ccpa-opt-out`
- 30-day deletion grace period with full data purge

**Monitoring**
- Rate limiting on authentication endpoints (5 attempts per 15 min)
- Anomaly detection for login patterns
- Automated lockout after failed authentication attempts
