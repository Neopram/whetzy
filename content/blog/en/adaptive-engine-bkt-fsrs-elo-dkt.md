---
title: "How we built an adaptive Python learning engine: BKT, FSRS, Elo — and DKT in an A/B cell"
slug: "adaptive-engine-bkt-fsrs-elo-dkt"
date: "2026-10-02"
lang: en
author: "Whetzy"
summary: "Four models, three of them live for everyone and one still running as an experiment — and why we're telling you which is which."
---

"Adaptive learning" gets used as a marketing word more often than an
engineering one. Here's what it actually means in Whetzy's backend, model by
model, and — because this matters for honesty, not just for engineering taste
— which of these are the default experience for every learner and which one
is still a live experiment we haven't rolled out to everyone.

## The three that run for every learner

- **BKT (Bayesian Knowledge Tracing)** — `app/services/engine/bkt.py`. Tracks
  the probability you've actually mastered a skill, updated after every answer
  (`bkt.update`). It's not "you got it right, move on" — it's a probability
  that gets revised by evidence, including evidence that you got lucky on a
  guess.
- **FSRS (Free Spaced Repetition Scheduler)** — `app/services/engine/fsrs.py`.
  Decides when you see a skill again. `fsrs.review(card, grade, now)` takes
  your performance on a review and schedules the next one — the same family
  of algorithm behind modern spaced-repetition tools, applied to programming
  skills instead of flashcards.
- **Elo** — `app/services/engine/elo.py`. Every learner and every question has
  a rating; `elo.expected_score` predicts how likely you are to get a given
  question right before you answer it, and `elo.update` adjusts both ratings
  afterward based on whether that prediction held. This is what lets the
  question-picker aim for "hard enough to be useful, not so hard it's a coin
  flip."

Together, these three decide two things every time you open a lesson: which
skill you're ready to practice next, and which specific question — out of
however many exist for that skill — is the right difficulty for you right now.

## The one that's still an experiment: DKT

**DKT (Deep Knowledge Tracing)** — `app/services/dkt.py` — is a neural model
that predicts mastery from your full answer history, not just a per-skill
probability. It's real code, it runs, and it's wired into the quiz endpoint —
but only for users assigned to the `"dkt"` A/B cohort
(`app/services/quiz.py`: `if get_cohort(user.id) == "dkt": predictions =
_dkt.predict(history)`). Most learners are still on the BKT+FSRS+Elo path
above. We're not claiming DKT "powers Whetzy" — it powers one experiment
arm, and whether it beats the baseline is exactly what the A/B test is
there to answer. (A proper power analysis for that comparison — how many
users you need before the result means anything — is tracked in our own
backlog as a separate, not-yet-started piece of work.)

## Why this split matters more than the model names

The interesting engineering decision isn't "we used four models" — it's that
three of them are simple enough to reason about and audit (BKT's whole state
is one probability per skill; you can print it and it makes sense), and the
fourth, the one that's hardest to audit, is the one we haven't trusted with
everyone's experience yet. That's the actual lesson, if there's one to take
from this: the sophistication of a model and the confidence you should have
in shipping it to 100% of users are different axes, and conflating them is
how adaptive learning products ship things that look smart and perform worse
than a simple rule would have.

## Code that runs, not just code that's described

Every example above corresponds to a file in the running backend, not a
diagram. The code examples learners actually execute while studying — Python,
SQL, JavaScript — run the same way: in-browser, via WebAssembly (Pyodide for
Python, sql.js for SQL), not shipped off to a server and back.

---

*Whetzy (whetzy.com) — bilingual, adaptive Python→AI learning.*
