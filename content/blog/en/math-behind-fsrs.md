---
title: "The math behind FSRS: how Whetzy schedules programming reviews"
slug: "math-behind-fsrs"
date: "2026-10-02"
lang: en
author: "Whetzy"
summary: "FSRS replaces 'review every N days' with three numbers per skill — stability, difficulty, retrievability — and updates all three after every answer."
---

Most spaced-repetition tools still run on SM-2, the algorithm Anki shipped with
in 2006: fixed intervals, one "ease factor" per card, and not much else. Whetzy
runs **FSRS** instead — a model that replaces SM-2's one number with three,
updated from real data instead of a hand-tuned curve.

Our implementation (`app/services/engine/fsrs.py`) carries 21 weight slots
and labels itself FSRS-6 in its own docstring, but the last two (w19, w20 —
the parameters FSRS-6 added on top of FSRS-5 for short-term/same-day review
behavior) are hardcoded to `0.0` in our defaults. With those switched off,
what's actually running is FSRS-5's 19 active weights, padded to 21 slots —
not the full FSRS-6 model its own docstring claims. We're correcting that
here rather than in the code comment, which still needs fixing.

## What FSRS actually tracks, per skill

The `Card` dataclass holds two of the three numbers directly:

- **Stability** — roughly, how many days it'd take for your recall probability
  to drop to 90%. Higher stability, longer until you need another review.
- **Difficulty** — how hard this specific skill is for you specifically, not
  how hard it is in the abstract.

**Retrievability** — the model's current estimate of "if tested right now,
what's the probability you get it right" — is *not* a field on `Card`. It's
computed from stability and elapsed time at the moment of review and written
to `ReviewLog`, the per-review audit trail, not persisted as card state.

Every review updates all three, not just "was I right." The classic FSRS flow
has the learner self-report a 4-point grade — Again, Hard, Good, Easy. We
don't ask you to: Whetzy computes the grade for you, from whether you got the
question right and how fast relative to how long it should take
(`_grade_from_response` in `app/services/quiz.py`) — "right but it took
longer than expected" and "right, fast" land as different grades (Hard vs.
Easy) even though both are "correct," same as the self-reported version, just
measured instead of asked.

## Where the weights come from

FSRS's weights aren't ours — they're from the open-spaced-repetition project,
derived from fitting the model against roughly 700 million real Anki review
logs. That's the actual point of using FSRS over a hand-picked SM-2 ease
factor: the curve describing how memory decays was fit to how memory actually
decayed for hundreds of millions of real reviews, not guessed at by one
algorithm designer in 2006. The published claim behind FSRS (not something
we've independently re-measured on Whetzy's own review logs) is 20-30% fewer
reviews than SM-2 for the same retention — fewer repetitions wasted on things
you already had solid, because stability is tracked per-card instead of
inferred from one shared ease curve.

## Why this matters for programming, not just flashcards

FSRS was built for flashcards — vocabulary, trivia, anything with a clean
"did I remember this" signal. Programming skills are messier: "do you remember
list comprehensions" isn't one fact, it's a cluster of related judgments. What
we track per skill (not per individual question) is whether you've retained
the *skill*, with the actual questions drawn from Elo-rated difficulty within
that skill (see our post on the engine architecture) rather than FSRS trying to
model each question as its own independent memory.

## The honest caveat

We haven't published Whetzy-specific retention numbers comparing our FSRS
scheduling against a naive fixed-interval baseline — that would need a proper
A/B test with enough users to say something real, the same bar we're holding
the DKT experiment to. The 20-30% figure above is FSRS's own published
result from Anki data, not a Whetzy result, and we're saying so rather than
letting the citation blur into a claim about us.

---

*Whetzy (whetzy.com) — bilingual, adaptive Python→AI learning.*
