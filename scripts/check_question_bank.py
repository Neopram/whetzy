#!/usr/bin/env python3
"""Structural checks over the shipped question bank (task 10.2).

These catch the mistakes that are easy to make when a bank grows to thousands of
hand-authored questions and impossible to spot by reading: a duplicated id, a
question that lost its English half, an option list with a repeat, and - the one
that actually changes what a learner experiences - correct answers clustered on
one position.

That last check is not pedantry. Authoring Domain 1 of the AWS track by hand
produced 7/59/5/1 across the four positions: 82 % of answers were option B,
because writing a plausible wrong option first and the right one second is a
habit you do not notice. A learner who spots that scores well while knowing
nothing, and the mastery estimate becomes a lie - which is red line 1.

No network access, so unlike scripts/check_content_sources.py this can run in
CI. Run it after changing the bank:

    python scripts/check_question_bank.py
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "questions"

# Below this many questions, position counts are noise rather than a pattern.
SKEW_MIN_SAMPLE = 40
SKEW_MAX_SHARE = 0.45
MIN_PER_SKILL = 6

# Density the adaptive engine actually needs, as opposed to the floor above.
#
# Taking a skill to mastery costs roughly 10-15 attempts of BKT evidence. Below
# that many items per skill the learner meets the same question again before
# mastering the concept, starts recognising the answer rather than knowing it,
# and `p_known` climbs on a memory of the option rather than of the idea. That
# is red line 1 broken from the content side, where no amount of engine work
# can fix it.
#
# It is a WARN, not a failure: the bank sits at ~8.0 today and closing the gap
# is authoring work measured in weeks. Ratchet it as tracks are filled in, so
# the number can only ever move forward.
TARGET_PER_SKILL = 15
# true/false balance: below this many in a track, the ratio is noise.
TF_MIN_SAMPLE = 25
TF_BAND = (0.35, 0.65)


def load() -> list[tuple[Path, dict]]:
    items = []
    for path in sorted(CONTENT.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for q in data.get("questions", data if isinstance(data, list) else []):
            items.append((path, q))
    return items


def main() -> int:
    items = load()
    problems: list[str] = []
    warnings: list[str] = []

    def fail(path: Path, qid: str, msg: str) -> None:
        problems.append(f"{path.relative_to(ROOT).as_posix()} [{qid}] {msg}")

    # --- ids unique across the whole bank, not just within a file ---
    seen: dict[str, Path] = {}
    for path, q in items:
        qid = q.get("id", "<no id>")
        if qid in seen:
            fail(path, qid, f"duplicate id, also in {seen[qid].name}")
        seen[qid] = path

    # --- bilingual parity (red line 3) and well-formed options ---
    for path, q in items:
        qid = q.get("id", "<no id>")
        for field in ("question_es", "question_en", "explanation_es", "explanation_en"):
            if not (q.get(field) or "").strip():
                fail(path, qid, f"{field} is empty - nothing ships in one language")
        if not (q.get("source") or "").strip():
            fail(path, qid, "no source - red line 2")

        opts_es, opts_en = q.get("options_es"), q.get("options_en")
        if opts_es is None and opts_en is None:
            continue  # open-ended types (fill_blank, *_exec) carry no options
        if not opts_es or not opts_en or len(opts_es) != len(opts_en):
            fail(path, qid, "option lists differ between languages")
            continue
        for side, opts in (("es", opts_es), ("en", opts_en)):
            if len(set(opts)) != len(opts):
                dupe = [o for o, n in Counter(opts).items() if n > 1][:1]
                fail(path, qid, f"repeated option in {side}: {dupe}")
        ci = q.get("correct_index")
        if ci is None or not (0 <= ci < len(opts_es)):
            fail(path, qid, f"correct_index {ci!r} out of range for {len(opts_es)} options")

    # --- answer position skew, per track ---
    #
    # true_false is measured separately below. Its two options are
    # Verdadero/Falso, so a lopsided distribution there is not a position
    # problem to be fixed by reordering (rendering "Falso, Verdadero" is just
    # odd) - it means too many statements were written to be true, which needs
    # rewriting. Mixing the two into one number hides both.
    by_track: dict[str, Counter] = defaultdict(Counter)
    tf_track: dict[str, Counter] = defaultdict(Counter)
    for path, q in items:
        ci = q.get("correct_index")
        opts = q.get("options_es")
        if ci is None or not opts:
            continue
        if q.get("type") == "true_false":
            tf_track[path.parent.name][ci] += 1
        else:
            by_track[path.parent.name][ci] += 1

    for track, dist in sorted(by_track.items()):
        total = sum(dist.values())
        if total < SKEW_MIN_SAMPLE:
            continue
        worst, count = dist.most_common(1)[0]
        share = count / total
        if share > SKEW_MAX_SHARE:
            problems.append(
                f"{track}: {share:.0%} of multi-option answers sit at position {worst} "
                f"({count}/{total}) - guessable without knowing the material. "
                "Run scripts/rebalance_answer_positions.py"
            )

    # --- true/false balance, reported but not failed on ---
    #
    # Measured per track as well as overall: the first version of this check was
    # global only, and a global 59 % hid track03 sitting at 83 %. A learner
    # studies one track at a time, so the per-track number is the one that
    # describes what they actually experience.
    tf_all = Counter()
    for c in tf_track.values():
        tf_all.update(c)
    tf_total = sum(tf_all.values())

    def flag(label: str, dist: Counter) -> None:
        total = sum(dist.values())
        if total < TF_MIN_SAMPLE:
            return
        share_true = dist[0] / total
        if not TF_BAND[0] <= share_true <= TF_BAND[1]:
            side = "true" if share_true > 0.5 else "false"
            worst = dist[0] if side == "true" else dist[1]
            warnings.append(
                f"{label}: true/false questions are {max(share_true, 1 - share_true):.0%} "
                f"\"{side}\" ({worst}/{total}) - always answering {side} scores that much. "
                "Fixing it means rewriting statements, not reordering options"
            )

    if tf_total:
        flag("overall", tf_all)
    for track, dist in sorted(tf_track.items()):
        flag(track, dist)

    # --- per-skill floor ---
    per_skill = Counter(q.get("skill_id") for _, q in items)
    for skill, n in sorted(per_skill.items()):
        if n < MIN_PER_SKILL:
            problems.append(f"skill {skill} has {n} question(s); the floor is {MIN_PER_SKILL}")

    # --- engine density, per track ---
    # Reported per track because that is the unit authoring happens in, and
    # because the averages differ sharply: the certification track was built at
    # the right density while the original seven were not.
    # Counted over ALL questions, not just the ones with options. `by_track`
    # holds the answer-position distribution, so it only sees multiple choice;
    # dividing that subset by every skill in the track would report a density
    # well below the real one and send authoring after a phantom gap.
    skills_per_track: dict[str, set[str]] = {}
    questions_per_track: Counter[str] = Counter()
    for path, q in items:
        skill = q.get("skill_id")
        if not skill:
            continue
        # Same key as by_track, so the two columns line up on one row.
        skills_per_track.setdefault(path.parent.name, set()).add(skill)
        questions_per_track[path.parent.name] += 1

    print(f"\n[bank] {len(items)} questions across {len(by_track)} tracks, "
          f"{len(per_skill)} skills\n")
    for track, dist in sorted(by_track.items()):
        total = questions_per_track.get(track, 0)
        spread = "/".join(str(dist[i]) for i in range(4))
        n_skills = len(skills_per_track.get(track, ()))
        density = f"{total / n_skills:>5.1f}" if n_skills else "    -"
        mark = " " if not n_skills or total / n_skills >= TARGET_PER_SKILL else "*"
        print(f"  {track:<38} {total:>5} Q   {density} Q/skill{mark}  positions {spread}")

    overall_density = len(items) / len(per_skill) if per_skill else 0.0
    if overall_density < TARGET_PER_SKILL:
        short = int(TARGET_PER_SKILL * len(per_skill)) - len(items)
        warnings.append(
            f"bank density is {overall_density:.1f} Q/skill against a target of "
            f"{TARGET_PER_SKILL} (* marks the tracks below it). That is {short} more "
            "questions. Under-dense skills repeat before they are mastered, so "
            "p_known ends up measuring recall of the option rather than of the idea"
        )

    # Warnings are real findings that this tool is the wrong place to fail on:
    # they need authoring work, not a mechanical fix, so blocking CI on them
    # would just teach people to silence the tool.
    for w in warnings:
        print(f"\n  WARN  {w}")

    if problems:
        print(f"\n[bank] FAIL - {len(problems)} problem(s):\n")
        for p in problems[:40]:
            print(f"  {p}")
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more")
        print()
        return 1

    print("\n[bank] PASS - ids unique, both languages present, options well formed, "
          "no position skew\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
