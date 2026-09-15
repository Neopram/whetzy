#!/usr/bin/env python3
"""Spreads correct answers evenly across option positions (task 10.3).

Why this is needed: the bank was authored by hand, and hand-authoring clusters
the correct answer badly. Measured before this ran:

    track01_python_basics          217/63/4/1   -> 76 % on option A
    track02_python_intermediate    116/10/0/0   -> 92 % on option A
    track03_python_advanced        115/5/0/0    -> 96 % on option A
    track04_software_engineering    75/117/3/0  -> 60 % on option B
    track05_software_architecture   78/77/0/0   -> 50 % on option A
    track06_ai_fundamentals         57/122/1/0  -> 68 % on option B
    track07_ai_engineering          51/129/0/0  -> 72 % on option B

Nothing shuffles options: the API returns `options_es`/`options_en` in stored
order and QuizScreen renders them with `options.map((opt, i) => ...)`. So a
learner who always picked the first option scored 96 % on Python Advanced
knowing nothing at all. Every mastery number computed from those answers is
measuring position-guessing as much as knowledge, which is red line 1 - the
engine must never overstate what someone knows.

The fix is mechanical and content-preserving: swap the correct option with the
one at a target position derived from the question id. Swapping (not rotating)
leaves the other options where the author put them, the target is stable across
runs, and no wording changes - so this is reviewable as a diff and revertible.

Two deliberate exclusions:
  * `true_false` questions, whose two options are Verdadero/Falso - reordering
    them to read "Falso, Verdadero" is odd, and their imbalance (174 true vs 82
    false) is a content problem that needs rewriting statements, not swapping.
  * questions with no options (fill_blank, *_exec), which have no positions.

Usage:
    python scripts/rebalance_answer_positions.py --dry-run
    python scripts/rebalance_answer_positions.py
    python scripts/rebalance_answer_positions.py --out-dir <dir>

`--out-dir` writes the rewritten files into a staging tree instead of in place,
mirroring the layout under content/questions. It exists because on the Windows
machine this repo lives on, Controlled Folder Access blocks python.exe from
writing anywhere under Desktop, and it surfaces as a misleading
`OSError: [Errno 9] Bad file descriptor` rather than a permission error. Write
to a staging dir and copy the files in with the shell.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "questions"
SKIP_TYPES = {"true_false"}


def target_index(qid: str, n: int) -> int:
    return int(hashlib.sha256(qid.encode()).hexdigest(), 16) % n


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    out_dir = None
    if "--out-dir" in sys.argv:
        out_dir = Path(sys.argv[sys.argv.index("--out-dir") + 1]).resolve()
    before: dict[str, Counter] = defaultdict(Counter)
    after: dict[str, Counter] = defaultdict(Counter)
    moved = 0
    touched_files = 0

    for path in sorted(CONTENT.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        # Two container shapes live in content/: the original {"questions": [...]}
        # and a bare [...] list used by every track added from track08_clf_c02
        # onward. Reading only the first shape made this script crash on the
        # newer tracks - which are precisely the ones with the worst position
        # bias - so it had never run over them.
        questions = data if isinstance(data, list) else data.get("questions")
        if not questions:
            continue
        track = path.parent.name
        changed = False

        for q in questions:
            opts_es, opts_en = q.get("options_es"), q.get("options_en")
            if not opts_es or q.get("type") in SKIP_TYPES:
                continue
            current = q["correct_index"]
            before[track][current] += 1

            tgt = target_index(q["id"], len(opts_es))
            if tgt != current:
                for opts in (opts_es, opts_en):
                    opts[current], opts[tgt] = opts[tgt], opts[current]
                q["correct_index"] = tgt
                moved += 1
                changed = True
            after[track][q["correct_index"]] += 1

        if changed and not dry_run:
            destination = path if out_dir is None else out_dir / path.relative_to(CONTENT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            touched_files += 1

    print(f"\n{'(dry run) ' if dry_run else ''}moved {moved} correct answers"
          f"{'' if dry_run else f' across {touched_files} files'}\n")
    print(f"  {'track':<38} {'before':<16} {'after':<16}")
    for track in sorted(before):
        b = "/".join(str(before[track][i]) for i in range(4))
        a = "/".join(str(after[track][i]) for i in range(4))
        total = sum(before[track].values())
        worst_after = max(after[track].values()) / total if total else 0
        print(f"  {track:<38} {b:<16} {a:<16} worst {worst_after:.0%}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
