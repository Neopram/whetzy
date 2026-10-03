---
title: "Trademark Search & IP Disclaimers Research"
last_updated: "2026-10-02"
effective_date: "2026-10-01"
language: "en"
status: "DRAFT - For reference only; NOT a professional clearance search"
version: "1.1.0"
---

# Trademark Search & IP Disclaimers Research

## Attempted automated search, 2026-10-02 — real outcome, not a completed clearance search

**This is not legal advice and does not substitute a professional trademark clearance
search.** An attempt was made to query EUIPO, WIPO and USPTO directly for "Whetzy" using
automated HTTP fetches (no browser, no JavaScript execution, no CAPTCHA solving — CAPTCHA
solving was not attempted, by design). Exact outcome of each attempt:

| Database | URL tried | Result |
|---|---|---|
| EUIPO eSearch | `https://euipo.europa.eu/eSearch/#details/trademarks/results?query=Whetzy` | Fetched 2026-10-02: only the static header/nav/footer came back; results render via JavaScript the fetch cannot execute. **No result obtained.** |
| WIPO Global Brand Database | `https://branddb.wipo.int/en/similarname/results?name=Whetzy` | Fetched 2026-10-02: page shows an Altcha CAPTCHA widget; results load only after solving it and an authenticated API call. **No result obtained; CAPTCHA not attempted.** |
| USPTO (via markerapi.com, an unofficial free wrapper) | `http://www.markerapi.com/api/v1/trademarks/name/whetzy/status/all/start/0` | Fetched 2026-10-02: HTTP 302 to `api.worldtradingdata.com.s3-website-us-east-1.amazonaws.com` — the wrapper service appears defunct. **No result obtained.** |
| USPTO data mirror (Justia) | `https://trademarks.justia.com/search?q=Whetzy` | Fetched 2026-10-02: HTTP 403 (bot-blocked). **No result obtained.** |

**Conclusion of this attempt:** none of the three official registries (EUIPO, WIPO, USPTO)
could be queried headlessly for "Whetzy" — they require a real browser (JS execution) and,
for WIPO, solving a CAPTCHA. **A manual search by a human, in a browser, at the three URLs
below is still required before any filing decision** — and even a clean manual text search is
not a substitute for a professional clearance search (which checks phonetic/visual similarity
and adjacent classes, not just exact-string matches).

### Official databases to search manually

#### 1. European Union (EUIPO)
- **URL**: https://euipo.europa.eu/eSearchPlus/
- **Search Term**: "Whetzy"
- **Classes of Interest**: 41 (Educational services), 42 (Software development)

#### 2. United States (USPTO)
- **URL**: https://www.uspto.gov/trademarks/search/ (new Trademark Center: https://tmsearch.uspto.gov)
- **Search Term**: "Whetzy"
- **Classes of Interest**: 41 (Educational), 42 (Software)

#### 3. World Intellectual Property Organization (WIPO)
- **URL**: https://www.wipo.int/branddb/en/
- **Search Term**: "Whetzy"
- **Coverage**: International registrations

### One real finding worth a professional's attention (unverified against the primary source)

A general web search (2026-10-02, not the USPTO database itself — the direct query was
blocked as above) surfaced **WERKZY**, a live US trademark application:

- Serial number 90087397, owner Werkzy LLC (Greenwich, CT, a Delaware LLC), filed
  2020-08-01, International Class 035 (online database of job postings/staffing services) —
  **a different class from education/software**, so a direct conflict looks unlikely, but it
  is phonetically and visually close to "Whetzy" and should be flagged to the lawyer.
- Source: web search result summary citing `https://uspto.report/TM/90087397/` and
  `https://trademarks.justia.com/browse-by-serial-number/90/08/73/` (both direct fetches
  returned HTTP 403, so this is an **unverified secondary report, not a primary-source
  confirmation** — label: Likely, not Verified). The application's status ("Awaiting
  Examination" per the 2020 filing) is almost certainly stale by 2026; a human must re-check
  its current status directly.

---

## Trademark Registration Recommendation

### Current Status: MVP/DEV Phase
**Decision**: Do NOT register trademarks yet.

### Rationale
1. Product not launched: Whetzy is still in development
2. Cost: ~€1,200 for EU + US + Madrid
3. Timing: Register 2-4 weeks before public launch

### Recommended Timing
- Phase 1: Document evidence of use (website, social media)
- Phase 2: File trademark applications before launch
- Phase 3: Monitor for infringement

---

## IP Disclaimers Status

- ✅ ip-disclaimers.en.md — Already drafted
- ✅ ip-disclaimers.es.md — Already drafted

---

## Licenses Page Implementation

### Path: /licenses endpoint

Create bilingual pages with disclaimers for:
- AWS, Microsoft, Google, CompTIA, ISC2, PCI
- Python, SQL, JavaScript, PostgreSQL
- Open source licenses (CC BY, MIT, Apache, PSF)

### Files to Create
- frontend/pages/licenses.tsx (routes to language-specific version)
- Language toggle in footer to link to /en/licenses and /es/licenses

---

**Status**: DRAFT for reference — automated search attempted and documented 2026-10-02;
manual search by a human still pending (ledger 21.6)
**Generated**: 2026-09-19; actualizado 2026-10-02
