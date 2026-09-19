---
title: "AI Act, DSA, and EAA Compliance Assessment"
last_updated: "2026-09-19"
effective_date: "2026-10-01"
language: "en"
status: "DRAFT - Requires legal review"
version: "1.0.0"
---

# AI Act, DSA, and EAA Compliance Assessment

## Legal Disclaimer

**This is a DRAFT document for internal review only. It has NOT been reviewed or approved by legal counsel and should NOT be used in production or shared with users until formally approved.** The Service operator [LEGAL ENTITY PENDING — H.29] reserves all rights and is not liable for any use of this document without proper legal authorization.

---

## Executive Summary

Whetzy integrates an AI tutor (Groq \qwen/qwen3.8-27b\) for personalized learning content. This assessment documents obligations under three EU regulatory regimes:

1. **AI Act (2024/1689)** — Obligations for "providers" and "deployers" of AI systems
2. **Digital Services Act (2022/2065, DSA)** — Content moderation and platform transparency
3. **European Accessibility Act (EAA)** — Accessibility standards (as of 2025, emerging)

**Current Status**: AI Act applies if Whetzy reaches EU market; DSA likely exempt (no UGC); EAA emerging requirement.

---

## AI Act (2024/1689) — Core Obligations

### Whetzy's Role: "Deployer" vs "Provider"

**Definition**:
- **Provider**: Entity that develops the AI system. ← Whetzy uses third-party (Groq Qwen model)
- **Deployer**: Entity that uses the AI system in an EU context. ← **WHETZY IS THE DEPLOYER**

**Implication**: Whetzy must assume "deployer" obligations even though Groq is the provider.

### Risk Classification: What Category Is The Tutor?

The Qwen tutor is used to:
1. **Generate learning explanations** (grounded with course content)
2. **Respond to student questions** about Python, SQL, cybersecurity, cloud certifications
3. **Adapt question difficulty** (via BKT/FSRS, not AI decision alone)
4. **NOT**: Make employment, credit, visa, education eligibility decisions

**AI Act Classification**: **HIGH-RISK** (Art. 6)

Why? Qwen is used in educational context. Educational decisions on content/progression can affect learning outcomes. However, since Qwen does NOT make final eligibility decisions (human instructor does), it falls into **MEDIUM-RISK** more likely.

**Conclusion**: Treat as **HIGH-RISK** (educational context) → Requires:
- ✅ Risk assessment
- ✅ Transparency documentation
- ✅ Human oversight procedures
- ✅ User information about AI involvement

### Deployer Obligations (Whetzy-Specific)

#### 1. Risk Assessment & Mitigation (Art. 27)
**Required**:
- Document potential harms: Bias in explanations, factually incorrect responses, student overreliance
- Mitigation: Groq model is public (not trained on Whetzy data); grounded with course content; fallback to rules-based explanations if Groq fails
- Documentation: Store in docs/legal/ai-risk-assessment.md (TBD)

#### 2. Transparency to End Users (Art. 50)
**Required**: Inform users that AI tutor is used. Where?
- [ ] UI label: "AI-powered tutor" or "Powered by Groq" near responses
- [ ] Onboarding: "This app uses AI to generate learning explanations"
- [ ] Settings: Toggle to disable AI mode (use rule-based fallback)
- [ ] Privacy policy: Already mentions "Groq AI" for tutor responses
- [ ] Suggested location in code: rontend/components/TutorResponse.tsx (add \<AIPoweredBadge>\)

#### 3. Monitoring & Logging (Art. 27)
**Required**: Log AI decisions for audit.
- [ ] Store: Question ID + AI response + user feedback (thumbs up/down)
- [ ] Retention: 1 year for audit trail
- [ ] Schema: Add \i_tutor_log\ table with: user_id, question_id, groq_response, user_rating, timestamp

#### 4. Human Oversight (Art. 27)
**Required**: Humans can intervene/override AI.
- [ ] Content admins can flag poor AI responses
- [ ] Fallback: If Groq fails, rules-based system takes over
- [ ] Current: Admins can edit questions; implement \lag_ai_response\ endpoint

#### 5. Documentation (Art. 28, 29, 30)
**Required**: Keep documentation available for audits.
- [ ] AI system: Name (Qwen 3.8-27b), provider (Groq), purpose (learning explanation)
- [ ] Data: Inputs (question + user quiz attempt), outputs (explanation)
- [ ] Measures: Security (API key in env), privacy (no user data in Groq context), bias (no fine-tuning on user data)
- [ ] File: docs/legal/ai-system-documentation.md (TBD)

### Deployer Obligations: Label Requirement (Detailed)

**Art. 50(1)**: Users must be informed when interacting with AI-generated content.

**Suggested UI Implementation**:
`	sx
// frontend/components/TutorResponse.tsx
<div className="tutor-response">
  <div className="ai-badge">
    <Icon name="ai" />
    <span>AI-powered explanation</span>
  </div>
  <div className="response-content">
    {response.text}
  </div>
  <button onClick={toggleAiMode}>Use rule-based mode instead</button>
</div>
`

**Placement**: Above or below tutor response, always visible.

**Rationale**: Users need to know they're reading AI-generated text, not expert-authored.

---

## Digital Services Act (2022/2065) — Content Moderation Obligations

### Does Whetzy Fall Under DSA?

**DSA Scope**: Applies to "online platforms" that allow users to store/share content.

**Assessment**:

| Element | Whetzy Status | DSA Applicability |
|---|---|---|
| User-Generated Content (UGC) | NO — Whetzy is not social; no content sharing | **NO UGC** → Likely exempt |
| Social Features | NO — No messaging, comments, community posts | **NOT A PLATFORM** → Likely exempt |
| Algorithmic Curation | YES — BKT + FSRS ranks questions | **Algorithmic** → Applies if "intermediary" |
| Third-Party Profiles | NO — No user profiles, followers, etc. | **NOT SOCIAL** → Exempt |
| Moderation Requirements | N/A if exempt | **Conditional** |

**Conclusion**: Whetzy likely **EXEMPT** from DSA because it has **no user-generated content** and is not a social platform. However, if Whetzy adds user-authored content or community features, DSA obligations would activate.

### If Whetzy Were to Add UGC (Scenario for Compliance Roadmap)

**Obligations** (if DSA applies):
1. **Content Moderation Policy** — Publicly available rules on prohibited content
2. **Complaint Handling** — Process user complaints in 60-90 days
3. **Transparency Reports** — Publish quarterly/annual moderation stats
4. **Recommendation Algorithm Transparency** — Explain how content ranking works

**Current Status**: No action needed for MVP. Add to Phase 3 if community features added.

---

## European Accessibility Act (EAA) — Emerging Requirement

### EAA Scope & Timeline

**EAA (2019/882)**: Harmonizes accessibility requirements for digital services across EU.

**Applicability**: 
- Applies to: Websites, apps, ICT services (e.g., learning platforms)
- Timeline: Full compliance by **June 28, 2025** (for large enterprises); **June 28, 2030** (for SMEs)
- Definition of SME: < 250 employees, < 50M EUR revenue

**Whetzy Status**: Currently in-scope for **2030 deadline** (assumed SME status).

### EAA Requirements for Whetzy

#### 1. WCAG 2.1 Level AA Compliance (Core Requirement)
Whetzy's frontend must pass WCAG 2.1 AA:
- [ ] **Perceivable**: Text alternatives (alt text), captions for video, readable fonts, sufficient color contrast
- [ ] **Operable**: Keyboard navigation, no keyboard traps, sufficient time for interactions
- [ ] **Understandable**: Clear language, predictable navigation, error prevention
- [ ] **Robust**: Compatible with assistive technologies (screen readers, magnifiers)

**Current Status**: Vite + React PWA — needs accessibility audit. Recommend:
- [ ] Automated scan: WAVE, axe, Lighthouse
- [ ] Manual testing: Screen reader (NVDA, JAWS)
- [ ] Priority: Quiz interface, settings, export/delete flows

#### 2. Accessibility Statement (Required)
**Required**: Public statement on whetzy.com/accessibility explaining:
- Conformance level (WCAG 2.1 AA target)
- Known issues
- Contact: accessibility@whetzy.com for feedback
- Enforcement procedures (AEDE — European Accessibility Enforcement Authority)

#### 3. Reasonable Accommodations
**Required**: Users with disabilities can request accommodations.
- [ ] Font size adjustment
- [ ] Dark mode (already implemented)
- [ ] Text-to-speech for code examples
- [ ] Extended time for quizzes
- [ ] Process: accessibility@whetzy.com

### EAA Implementation Timeline

| Deadline | Action |
|---|---|
| 2026-12 (Recommended) | Accessibility audit; identify gaps |
| 2027-06 | Fix critical issues (keyboard, screen reader, contrast) |
| 2028-12 | Achieve WCAG 2.1 AA compliance |
| 2029-06 | Publish accessibility statement |
| 2030-06 | **Full compliance required** (SME deadline) |

---

## Compliance Checklist for Whetzy

### AI Act (Deployer Obligations) — 6-12 Months
**Priority**: HIGH (if marketing in EU)

- [ ] **Task 1**: Add "AI-powered" label to tutor responses (Code location: rontend/components/TutorResponse.tsx)
  - Effort: 4 hours
  - File: Create UI component \AIPoweredBadge.tsx\
  - Test: Manually verify on quiz, tutor, duel flows

- [ ] **Task 2**: Create \i-risk-assessment.md\ documenting harms & mitigations
  - Effort: 8 hours
  - File: docs/legal/ai-risk-assessment.md
  - Content: Risk register, mitigation strategies, audit trail

- [ ] **Task 3**: Implement AI response logging for audit trail
  - Effort: 12 hours
  - Schema: Add \i_tutor_audit_log\ table (user_id, question_id, groq_response, user_feedback, timestamp)
  - Code: ackend/app/models/ai_audit.py + endpoint to flag poor responses

- [ ] **Task 4**: Implement rule-based fallback toggle in settings
  - Effort: 6 hours
  - UI: Settings page toggle "Use AI explanations"
  - Logic: If disabled, routes to rules-based system (existing fallback)

### DSA (Content Moderation) — 0 Months (Conditional)
**Priority**: LOW (unless UGC added)

- [ ] Defer: No action if Whetzy remains a non-social learning app
- [ ] Activate if: Community features, user forums, or student-authored content added

### EAA (Accessibility) — 36+ Months (SME Timeline)
**Priority**: MEDIUM (2030 deadline)

- [ ] **Task 1**: Accessibility audit (WCAG 2.1 AA)
  - Effort: 20 hours
  - Tool: WAVE, Lighthouse, axe
  - Target: 2026-Q3

- [ ] **Task 2**: Fix critical issues
  - Effort: 40-60 hours (estimate; depends on audit findings)
  - Priority: Keyboard nav, screen reader, color contrast
  - Target: 2027-Q2

- [ ] **Task 3**: Publish accessibility statement
  - Effort: 4 hours
  - File: rontend/public/accessibility.md → \/accessibility\ route
  - Target: 2029-Q2

---

## Summary: Regulatory Obligations

| Regulation | Applicability | Key Obligation | Whetzy Action | Timeline |
|---|---|---|---|---|
| **AI Act** | **YES** (if EU users) | Deployer transparency + risk mgmt | AI labels + audit log + documentation | 6-12 mo |
| **DSA** | **NO** (no UGC) | Content moderation (if social) | Defer until UGC added | N/A |
| **EAA** | **YES** (SME 2030) | WCAG 2.1 AA compliance | Audit + fixes + statement | 36+ mo |

---

**Status**: DRAFT for legal review
**Generated**: 2026-09-19
