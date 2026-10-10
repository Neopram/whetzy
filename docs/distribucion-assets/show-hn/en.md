# Show HN (EN) — ledger 27.1

Preparation + assets only. Posting under the owner's own Hacker News account is
"Solo el dueño" (H.45) — this file is the copy-paste kit, nothing here gets
submitted by this session.

Source: `docs/DISTRIBUCION.md` §8 ("Hacker News") — same title and timing already
agreed there; this file expands it into something that's actually ready to paste.

## Title

`docs/DISTRIBUCION.md` §8 spec'd "I built an adaptive Python→AI learning
engine in Spanish because no one else did" — that's 80 characters on its
own, but HN's 80-char limit applies to the title **as submitted**, and HN
prepends "Show HN: " (9 chars) to every Show HN post, making the real total
89. Trimmed to fit under 80 with the prefix (flagged by [S5] in PR #93
review); also dropped the "because no one else did" claim — we only know
what we didn't find in our own search (see the hedged "as far as I could
find" phrasing in the body below), not that nothing like this exists:

```
I built an adaptive Python-to-AI engine, in Spanish
```

68 characters + "Show HN: " (9) = 77, under the limit.

## URL

`https://whetzy.com` — not `whetzy.com/en`: that path doesn't exist
(`App.tsx` has no route for it). The real landing is `/landing`, English via
`?lang=en` (`LandingScreen.tsx`); the root domain already resolves to it, so
plain `whetzy.com` is the right link, no query string needed.

## First comment (post immediately after submitting — HN rewards the OP explaining the "why")

> Hi HN. I'm the solo builder behind Whetzy (whetzy.com) — an adaptive Python→AI
> learning platform. The "why Spanish" part: most adaptive ed-tech (Duolingo-style
> spaced repetition + mastery tracking, not just video courses) ships English-only
> and treats other languages as an afterthought — if they exist at all. Spanish has
> ~500M speakers and, as far as I could find, nothing built content-native (not
> machine-translated) with a real adaptive engine underneath.
>
> Under the hood: BKT (Bayesian Knowledge Tracing) decides what you're ready for,
> FSRS schedules reviews so you don't forget it, and code examples run in-browser
> — Python and SQL via WebAssembly (Pyodide/sql.js), JS in a sandboxed Web Worker
> — no server round-trip to execute a snippet.
>
> It's free to use — the free tier's current limit is 5 lessons and 30 new
> questions a day; spaced-repetition reviews are unlimited for everyone. I'd genuinely like the
> HN read on where the adaptive-learning space is thin, what you'd want from a
> "serious" coding platform that a bootcamp or a YouTube series doesn't give you,
> and where this breaks for you if you try it. Happy to answer anything about the
> engine, the bilingual content pipeline, or the economics of building this solo.

## Timing

Tuesday or Wednesday, 9am EST (`docs/DISTRIBUCION.md` §8 — peak HN traffic window).
Do NOT post Friday–Sunday (confirmed low-traffic days for Show HN, general HN
community knowledge, not independently re-verified this session).

## Realistic expectation (already set in `DISTRIBUCION.md`, repeated here so
whoever posts doesn't anchor on vanity numbers)

50–200 upvotes, 20–50 new users. This is a planning assumption, not a measured
result — there is no live HN post yet to measure.

## What NOT to do (HN is adversarial to anything that smells like marketing)

- Don't post from a brand-new account with no history — HN's ranking algorithm
  and the community both penalize that.
- Don't ask friends to upvote in the first hour — HN's vote-ring detection flags
  coordinated voting and can kill the post's visibility silently.
- Don't argue in the comments. Answer technical questions plainly; if someone's
  skeptical about the "adaptive" claim, point at BKT/FSRS specifics, not adjectives.
- No invented metrics in the post or the comments. If a number isn't in this repo
  with a citation, don't say it — including in replies written in the moment.

## Checklist before the owner posts

- [ ] HN account aged — a brand-new account for this is a known red flag (community rule, see above)
- [ ] whetzy.com loads clean, no broken onboarding (same CI check that gated 31.8's kit)
- [ ] Owner has 2–3 hours free right after posting to answer comments — HN's algorithm
      rewards early engagement, and a dead thread looks worse than no thread
- [ ] Reconfirm the free-tier limit cited above (5 lessons / 30 questions a day)
      still matches both production's `FREE_DAILY_QUOTA_ENABLED`
      (`backend/app/core/config.py:244`) and the landing page
      (`frontend/src/i18n/{es,en}/common.json`) before posting
