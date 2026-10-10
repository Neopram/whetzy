---
title: "From 0 to ~11,000 questions: how we built Whetzy's content bank"
slug: "from-0-to-10000-questions"
date: "2026-10-02"
lang: en
author: "Whetzy"
summary: "How a 35-track, 727-skill question bank gets built without a content team — and how we keep the number honest."
---

Title says "~11,000", not the "10,000+" we used to say. Here's why that number
moved, and why we're telling you how we counted it instead of just stating it.

## The actual count, right now

```
find content/questions -name "*.json" | wc -l   # 271 files
```

Summing every question array across those 271 files gives **10,984** questions,
spread across **35 tracks** and **727 skills** — and as of today, **727/727
skills (100%) have at least one lesson** written for them (our own test suite
prints that line every run: `[lessons] 727/727 skills have a lesson`).

We're calling the question count "~11,000" and not "10,984" on purpose: it's a
snapshot from one `find` + `json.load` pass over the content tree, not a
number our backend serves from an API. It'll be a different number by the time
you read this — tracks get added, content gets reclassified, some questions
get retired for quality reasons. We'd rather round down and be right than
round up and be wrong.

## Why "how we counted it" matters more than the number itself

A 10,000-question bank that's 90% low-quality filler is worse than a
1,000-question bank where every item actually discriminates between "knows it"
and "doesn't." Quantity is the easy part — anyone can generate plausible-looking
quiz questions with an LLM. The actual engineering work was building a gate
that catches the filler before it ships:

- **A content QA pipeline** (`scripts/content_qa/`) that reviews every batch
  before it's considered done — not a spellcheck, an adversarial pass that
  looks for exactly the failure modes LLM-written questions fall into
  (ambiguous phrasing, more than one defensible correct answer, an explanation
  that doesn't actually explain).
- **A pilot-first policy before scaling any writer.** The project's own rule:
  before trusting a content-writing model with a full batch, it runs a 10-item
  pilot. If more than 3 of 10 come back flagged `blocker` or `major`, the run
  stops and a human decides — this isn't hypothetical, an actual pilot batch
  failed that bar (7 of 10 flagged) and got stopped before it touched the live
  bank.
- **Executable questions get actually executed.** Where a question claims code
  runs a certain way, there's a test that runs that code and checks the claim
  — not a human eyeballing the snippet. Python questions run in a CPython
  subprocess, SQL questions against CPython's own `sqlite3` module — both
  mirroring what the browser does rather than literally running inside it.
  A small set of Playwright end-to-end tests then confirms the real
  in-browser sandboxes (Pyodide, sql.js) actually initialize and execute
  correctly, separately from the per-question gate.

## What this means if you're building something similar

If your content pipeline's only quality signal is "an LLM wrote it and it
looked fine," you don't have a quality signal — you have a vibe. The gate has
to be something you can point at and say "this specific check caught this
specific class of error," and it has to be something you can *break on purpose*
to confirm it's actually catching anything. A check nobody has ever seen fail
is a check nobody's verified works.

---

*Whetzy (whetzy.com) is a bilingual, adaptive Python→AI learning platform.
Code examples run in-browser via WebAssembly — no external sandbox.*
