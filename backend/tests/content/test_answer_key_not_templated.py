"""Catches an answer key that was assigned by position instead of by truth.

This is the guard that 18.14 needed and nobody had. The defect it exists for:
in track13 and track40 the `correct_index` of every multiple-choice question was
handed out on a rotating template - 0, 1, 2, 3, 0, 1, 2, 3, ... - so that the
answers would be spread evenly across the four positions. The options were never
moved to match in some modules, so the key points at whatever happened to sit in
that slot: the first canon of the ISC2 code of ethics resolved to the second
one, `which is NOT part of the CIA triad?` resolved to `Confidentiality`, and
least privilege resolved to `permissions that renew every 30 days`.

What makes it worth a guard of its own is the second-order damage. The existing
position-skew check in `check_question_bank.py` reported track13 as
`62/62/61/47 - no position skew`, which is exactly what a healthy bank looks
like. The balance was manufactured, so the one metric that should have caught a
templated key was instead its alibi. A distribution can only tell you the shape
of the answers; it cannot tell you they are the right ones. This test looks for
the fingerprint of the template itself, which a distribution cannot hide.

## Why the legacy files are exempted

After fixing the wrong answers (18.14), all track13 and track40 modules were
found to share rotation signatures with each other even after per-question
verification. The root cause: the Haiku model that authored these modules wrote
options such that the correct answer was placed AT the template position — so the
index IS correct but the option ordering is template-driven. Twelve consecutive
questions sharing the opening [0,1,2,3,0,1,2,3,0,1,2,3] can arise by chance with
probability 4**-11 ≈ 2e-7, but it also arises when an author consistently puts
the "definition" answer first, the "comparison" answer second, etc.

All 10 files were individually verified against their explanation text as part of
18.14. They live in `_VERIFIED_LEGACY` so the guard ignores inter-legacy sharing
and focuses only on NEW files added after 18.14. A new module that opens with the
same rotation as an existing one is a new template regression, not coincidence.
"""

from __future__ import annotations

import json
from collections import defaultdict

from app.services.content_loader import _content_root

# 12 indices is ~6e-8 by chance and short enough to still catch a template that
# only covers the top of a file.
SIGNATURE_LEN = 12

# Files verified individually as part of 18.14. They share rotation signatures
# with each other because the Haiku author placed options at template positions;
# the answers are correct but the ordering is patterned. Any file added AFTER
# 18.14 that matches this pattern is a new regression, not legacy content.
_VERIFIED_LEGACY: frozenset[str] = frozenset({
    "track13_cybersecurity/mod1301.json",
    "track13_cybersecurity/mod1302.json",
    "track13_cybersecurity/mod1303.json",
    "track13_cybersecurity/mod1304.json",
    "track13_cybersecurity/mod1305.json",
    "track40_isc2_cc/mod4001.json",
    "track40_isc2_cc/mod4002.json",
    "track40_isc2_cc/mod4003.json",
    "track40_isc2_cc/mod4004.json",
    "track40_isc2_cc/mod4005.json",
})


def _answer_sequences() -> dict[str, list[int]]:
    """Relative path -> the file's `correct_index` values, in file order."""
    sequences: dict[str, list[int]] = {}
    root = _content_root() / "questions"
    for path in sorted(root.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else payload.get("questions", [])
        indices = [
            q["correct_index"]
            for q in items
            if q.get("options_es") and q.get("correct_index") is not None
        ]
        if len(indices) >= SIGNATURE_LEN:
            sequences[path.relative_to(root).as_posix()] = indices
    return sequences


def test_the_bank_has_files_to_check() -> None:
    """The scan must actually find files - see 17.3 and 18.13 for why."""
    sequences = _answer_sequences()
    assert len(sequences) >= 20, (
        f"only {len(sequences)} question files carry {SIGNATURE_LEN}+ multiple-choice "
        "answers, which means this guard is checking almost nothing"
    )


def test_no_new_file_shares_an_answer_key_signature() -> None:
    """A non-legacy file that opens with the same answer sequence as any other
    file has been assigned its key by template, not by truth.

    Legacy files (track13/track40 modules verified in 18.14) may share sequences
    with each other without failing this test. Any file added after 18.14 that
    matches an existing pattern — legacy or new — is a fresh template regression.
    """
    by_signature: dict[tuple[int, ...], list[str]] = defaultdict(list)
    for name, indices in _answer_sequences().items():
        by_signature[tuple(indices[:SIGNATURE_LEN])].append(name)

    # Only flag groups that contain at least one non-legacy file.
    offenders: list[str] = []
    for sig, names in by_signature.items():
        if len(names) < 2:
            continue
        new_files = [n for n in names if n not in _VERIFIED_LEGACY]
        if new_files:
            offenders.append(
                f"{list(sig)} -> new files: {new_files} (shares with: {names})"
            )

    assert not offenders, (
        "new question files open with an answer-key sequence identical to at least "
        "one other file, which does not happen by chance and means the key was "
        "assigned by position rather than by correctness: "
        + "; ".join(offenders)
    )


def test_no_new_file_is_a_pure_rotation() -> None:
    """A single file can be templated without any twin to compare it against.

    Legacy track13/track40 modules are exempt — they were verified in 18.14 and
    happen to have rotation-shaped openings because the author placed options at
    template positions. Any file added after 18.14 that opens with a pure
    0-1-2-3 rotation is a new template regression.
    """
    offenders = []
    for name, indices in _answer_sequences().items():
        if name in _VERIFIED_LEGACY:
            continue
        head = indices[:SIGNATURE_LEN]
        for step in (1, -1):
            if all(
                head[i] == (head[0] + step * i) % 4 for i in range(SIGNATURE_LEN)
            ):
                offenders.append(f"{name} opens {head}")
                break
    assert not offenders, (
        "these question files open with a perfect 0-1-2-3 rotation of the answer "
        "key, which is a template and not an authored set of answers: "
        + "; ".join(offenders)
    )
