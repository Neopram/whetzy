---
title: "Cookie Policy"
last_updated: "2026-09-19"
effective_date: "2026-10-01"
language: "en"
status: "DRAFT — pending professional legal review (H.20)"
version: "1.0.0"
---

# Cookie Policy

## Legal Disclaimer

**DRAFT — pending professional legal review (H.20).**

**This is a DRAFT document for internal review only. NOT reviewed/approved by legal counsel. DO NOT use in production.**

---

## 1. What Are Cookies?

Cookies are small text files stored on your device that help personalize your experience. They contain information about your browsing behavior and preferences.

---

## 2. Types of Cookies We Use

### 2.1 Essential Cookies (Always Active)

These cookies are necessary for basic functionality:

- **Session Identifier**: Unique ID for your session
  - Name: `whetzy_session`
  - Duration: Session (expires on logout)
  - Purpose: Maintain login state

- **Authentication Token**: Secure token for authentication
  - Name: `whetzy_auth`
  - Duration: 30 days (configurable)
  - Security: HttpOnly, Secure, SameSite=Strict
  - Purpose: Verify user identity

- **CSRF Protection**: Cross-Site Request Forgery token
  - Name: `whetzy_csrf`
  - Duration: Session
  - Purpose: Prevent unauthorized requests

- **Language/Preference**: User preferences
  - Name: `whetzy_lang`, `whetzy_theme`
  - Duration: 1 year
  - Purpose: Remember language and theme settings

### 2.2 Analytics Cookies (Optional)

Used to understand user behavior and improve service:

We do not currently use any third-party analytics cookies: no analytics tool of any kind is integrated in the production codebase.

### 2.3 Third-Party Cookies

We may also allow:

- **Payment Processor** (Stripe): Track transactions (currently test mode only, no live charges)
- **CDN Provider**: Cloudflare

---

## 3. Cookie Attributes

All our cookies use security best practices:

| Attribute | Description |
|-----------|-------------|
| **HttpOnly** | Cannot be accessed by JavaScript (prevents XSS attacks) |
| **Secure** | Transmitted only over HTTPS connections |
| **SameSite** | Prevents CSRF attacks; set to Strict or Lax |
| **Domain** | `.whetzy.com` (accessible across subdomains) |
| **Path** | `/` (accessible across entire application) |

---

## 4. Cookie Consent and Control

### 4.1 Implied Consent

By continuing to use Whetzy after being notified of this policy, you consent to our use of cookies. Essential cookies are always active.

### 4.2 Explicit Opt-In (if required)

In some jurisdictions, we provide explicit cookie consent via banner:
- Accept All: Enable all cookies
- Essential Only: Disable analytics cookies
- Customize: Choose specific categories

### 4.3 Disable Cookies

**Via Browser Settings:**
1. Open browser preferences/settings
2. Find "Privacy & Security" or "Cookies"
3. Select "Block all cookies" or manage individual sites
4. Reload Whetzy

**Specific Browsers:**
- **Chrome**: Settings > Privacy and security > Cookies
- **Firefox**: Preferences > Privacy > Cookies and Site Data
- **Safari**: Preferences > Privacy > Manage Website Data
- **Edge**: Settings > Privacy > Cookies

**Note**: Disabling cookies may limit Service functionality.

### 4.4 Opt-Out of Analytics

- Click "Manage Preferences" in cookie banner
- Disable "Analytics Cookies"

---

## 5. Do Not Track (DNT)

We do not currently respond to browser DNT signals. However, you can:
- Disable cookies (see above)
- Opt-out of analytics
- Contact us for additional privacy measures

---

## 6. Third-Party Cookies

| Service | Purpose | Cookies | Opt-Out |
|---------|---------|---------|---------|
| Stripe | Payment processing (currently test mode only, no live charges) | `__Secure-stripe_sid`, others | https://stripe.com/cookies-policy |
| CloudFlare | CDN/security | `__cfduid`, others | https://cloudflare.com/cookie-policy |

---

## 7. Changes to This Cookie Policy

We may update this policy periodically:
- Changes posted here
- Effective date updated
- Material changes: email notification
- Continued use = acceptance

---

## 8. Contact

For questions about cookies:

**Email**: legal@whetzy.com
**Support**: support@whetzy.com

---

**Version**: 1.0.0 (DRAFT)

**DRAFT NOTICE**: Not approved by legal counsel. Do not use in production.
