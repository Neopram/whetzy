# Affiliation Dossier — Python Institute & CompTIA

*September 2026 · Internal document*

---

## Objective

Establish affiliate programs with **Python Institute** (PCEP, PCAP, PCPP
certifications) and **CompTIA** (Security+, Network+, A+) to earn commissions
on exams purchased by our users through referral links.

## 1. Python Institute

### Relevant certifications

| Certification | Whetzy Track | Exam price | Level |
|---|---|---|---|
| **PCEP** — Python Certified Entry-Level Programmer | track01 (Python Basics) | ~$59 | Entry |
| **PCAP** — Python Certified Associate in Python Programming | track02 (Python Intermediate) | ~$295 | Associate |
| **PCPP** — Python Certified Professional in Python Programming | — (future) | ~$195 | Professional |

### Affiliate program

- **Platform**: Python Institute manages its affiliate program through
  Pearson VUE (exam provider).
- **Estimated commission**: 10-15% per exam sold through the affiliate link.
  [Guessing — verify directly with Python Institute before publishing figures.]
- **Expected requirements**:
  - Registered company or educator account.
  - Description of the platform and how it prepares candidates.
  - Acceptance of affiliate program terms.
- **Contact**: partners@pythoninstitute.org (verify at pythoninstitute.org).

### Steps to apply

1. Visit the Python Institute website and find the partners/affiliates section.
2. Complete the application form with:
   - Company information (Whetzy).
   - Product description and target audience.
   - Estimated candidate volume (based on active users).
3. Receive approval and affiliate links.
4. Integrate links into the Whetzy UI (certification screen, readiness
   meter results).

## 2. CompTIA

### Relevant certifications

| Certification | Whetzy Track | Exam price | Level |
|---|---|---|---|
| **Security+ SY0-701** | track08 (Cybersecurity) | ~$404 | Professional |
| **Network+ N10-009** | — (future) | ~$369 | Professional |
| **A+ 220-1101/1102** | — (future) | ~$258×2 | Entry |

### Affiliate program

- **Platform**: CompTIA has a partners program and marketplace.
- **Estimated commission**: ~10% per exam voucher purchase through the link.
  [Guessing — verify directly with CompTIA before publishing figures.]
- **Partnership types**:
  - **Authorized Delivery Partner**: requires physical exam facilities.
  - **Content Partner / Affiliate**: more suitable for Whetzy — preparation
    platform that refers candidates to the exam.
- **Contact**: partners@comptia.org or through comptia.org/partners.

### Steps to apply

1. Visit comptia.org and find the partners section.
2. Apply for the Content Partner or Affiliate program.
3. Provide:
   - Company information.
   - Description of preparation tracks.
   - User metrics (when available: active users, completion rate).
4. Receive approval and vouchers/affiliate links.
5. Integrate into Whetzy's certification screen.

## 3. Revenue model

| Scenario (month 6) | Users taking exam | Avg exam | Commission | Monthly revenue |
|---|---|---|---|---|
| Conservative | 20 | $150 | 10% | $300 |
| Moderate | 50 | $200 | 12% | $1,200 |
| Optimistic | 100 | $250 | 15% | $3,750 |

**Note**: commission figures are estimates. Actual percentages are negotiated
when formalizing the affiliation. Do not publish in any external document until
written confirmation from the provider is obtained.

## 4. Technical integration

- **UI**: "Register for the exam" button on the certification screen
  (`CertificationScreen`) with parameterized affiliate link.
- **Tracking**: UTM params or affiliate ID in the link for attribution.
- **Readiness meter**: "Your estimated probability of passing PCEP is X%.
  Ready to register?" with direct link.
- **Disclaimer**: "Whetzy is not an exam center. The exam is taken through
  the official provider."

## 5. Immediate actions

- [ ] Contact Python Institute (partners/affiliates).
- [ ] Contact CompTIA (Content Partner program).
- [ ] Obtain written confirmation of commission rates.
- [ ] Integrate affiliate links into the UI when available.
- [ ] Configure conversion tracking.
