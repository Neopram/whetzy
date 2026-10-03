---
title: "Whetzy vs. the catalog platforms — an honest comparison"
slug: "honest-comparison"
date: "2026-10-02"
lang: en
author: "Whetzy"
summary: "We compare against what we've actually re-checked on each competitor's own pricing page, not what we assume about them."
---

The ledger item behind this post asked for "an honest comparison against
Coursera and Udemy." We're not publishing one — and the reason why is itself
the point of calling this comparison "honest."

## Why Coursera and Udemy aren't in this table

We checked. Udemy's pricing page returns a 403 to automated access every time
we've tried (most recently today, 2026-10-02) — we have no independently
re-verified figure for it. Coursera Plus pricing exists only as a figure an
earlier research pass reported but never re-downloaded and confirmed against
the live page (tracked internally as "probable," not "verified" — see
`docs/COMPETENCIA.md` §A.2). Publishing a specific dollar figure for either of
them here, in a page whose entire premise is "we only show what we checked,"
would undercut that premise on the first row.

So instead, here's the comparison we can actually stand behind — the same one
`whetzy.com`'s own landing page shows, built from `frontend/src/lib/comparison.ts`
and checked `2026-09-24` (that date is a constant in the code, not a claim we're
making up for this post — change the table, change the date, there's a test for
it).

## What we checked, and where

| | Whetzy | Codecademy | Platzi | EDteam |
|---|---|---|---|---|
| Site in Spanish | Yes | No (`codecademy.com/es` redirects to the English home) | Yes | Yes |
| Free plan | Yes, no time limit | Basic, limited | Some courses free | 9 free courses |
| Monthly (USD) | $14.99 (Pro) | $29.99 | $49 | $30 |
| Yearly, per month (USD) | No yearly plan yet | $14.99 | ≈$21 ($249/yr) | $20 ($240/yr) |

Every one of those competitor figures comes from re-downloading the pricing
page directly on 2026-09-24 and reading the price out of the page's own
structured data (JSON-LD or inline pricing object) — not a screenshot, not a
summary from a research agent. `docs/COMPETENCIA.md` §A.1 has the exact quote
and URL for each cell.

## The actual difference, not just the price

Price alone doesn't say much without what you get for it. The thing we think
is worth saying plainly: Codecademy's `/es` path is a redirect, not a Spanish
product — if "Spanish-native" matters to you, read that row twice. Platzi and
EDteam do serve Spanish content, and we're not claiming otherwise; the
difference we'd point to is the adaptive engine (BKT decides what you're ready
for, FSRS schedules when you review it) versus a fixed course sequence, and
in-browser code execution (Pyodide/sql.js WebAssembly for Python and SQL, a
sandboxed Web Worker for JavaScript — no external sandbox for any of them)
versus embedded IDEs that call out to a server.

## If you want the Coursera/Udemy numbers

So do we. When someone re-downloads those pricing pages and reads an actual
figure off them — not an estimate, not something an automated crawl got
blocked trying to fetch — this table grows by two rows and the date updates.
Until then, a comparison that's missing two competitors on purpose is more
honest than one that has all of them with a number we can't stand behind.

---

*Whetzy (whetzy.com) — bilingual, adaptive Python→AI learning. Pricing per
`docs/DECISIONS.md` ADR-41/49; subject to change.*
