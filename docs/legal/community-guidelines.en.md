---
title: "Community guidelines and how to report"
last_updated: "2026-10-02"
effective_date: "pending publication"
language: "en"
status: "DRAFT — pending professional review (H.20) and owner confirmation of the support contact"
version: "1.0.0"
---

# Community guidelines and how to report

**DRAFT — not published.** No user sees this text yet; it is not loaded by any i18n key or
app route. It is written to cover the minimum Apple App Store Review Guideline **1.2 / 1.2.1**
(user-generated content) requires: at least one of objectionable-content filtering, a report
mechanism, the ability to block, or published contact information. Confirmed in
`docs/store/app-store-review-checklist.md` (rows 1.2 and 1.2.1, 2026-09-30): none of the four
exist today.

## 1. What this covers

The `username` and `display_name` a person chooses at signup are the only text another user
can see today in Whetzy: in duel challenges (you challenge someone by `username`, it appears
in the push notification "X challenged you to a duel") and in league leaderboards. Whetzy has
no forums, comments, messages, or content a user publishes for others to read — these
guidelines cover only the chosen name.

## 2. What is not allowed in a username or display name

- Insults, hate speech, or harassment directed at a person or group.
- Impersonating another person, Whetzy, or its team.
- Explicit sexual, violent, or illegal content.
- A third party's contact information without their permission.

## 3. How to report a username

If you see a username or display name that violates the above, email
**[SUPPORT CONTACT PENDING CONFIRMATION — `support@whetzy.com` appears today in
`docs/legal/dpa.en.md` §12, but no one has confirmed it is the mailbox that will be published
for this purpose]** with the exact username and, if possible, a screenshot. We review it and,
if warranted, change or remove the name.

**This is a manual process today.** There is no in-app "report" button or automated endpoint
yet — that is pending engineering work (ledger 19.11, outside my territory:
`backend/app/api/v1/endpoints/duels.py` and `admin.py`). This text does not claim that button
exists.

## 4. Blocking another user

The app **does not** have a block-user feature today. If you want to avoid being challenged
by a specific person, email the same support contact from point 3 and we will handle it
manually until the feature exists in the app.

## 5. What we do with a report

We review the reported name against the rules in point 2. If it violates them, we replace it
with a generic name and notify the corresponding account by email. Repeated violations may
lead to account suspension.

---

**Status**: DRAFT, not published. Pending: (a) owner confirmation of the contact mailbox;
(b) professional review (H.20); (c) engineering's (S1) decision on whether this lives in
`frontend/src/i18n/{es,en}/legal.json` as its own page or inside the published Terms, and
whether it builds the report/block endpoint that would replace the manual process in point 3.
