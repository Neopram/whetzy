#!/usr/bin/env python3
"""Re-fetches every URL cited by a question's `source` field (task 10.2).

Red line 2 says the tutor must never invent a citation, and the same standard
has to apply to the question bank: a question whose source points at a page that
does not exist is worse than one with no source at all, because it looks
checked. This is the check that makes "verified" mean something.

The AWS certification bank cites URLs, so it can be verified automatically. The
seven learning tracks cite books, PEPs and papers ("Pro Git 2e, Ch. 2"), which
no script can confirm - those were authored against the texts and would need a
human sampling to audit. This tool therefore reports how many sources it could
not check, rather than passing over them in silence.

Network access required, so this is deliberately NOT in CI: a third-party
outage must not turn the build red. Run it when the bank changes.

Usage:
    python scripts/check_content_sources.py             # every track
    python scripts/check_content_sources.py track08     # one track
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

CONTENT = Path(__file__).resolve().parent.parent / "content" / "questions"
URL_RE = re.compile(r"https?://[^\s)]+")
TIMEOUT = 20
# A plain urllib request with no User-Agent is rejected by several docs sites.
HEADERS = {"User-Agent": "whetzy-content-source-check/1.0 (+https://whetzy.com)"}


def load_questions(track_filter: str | None) -> list[dict]:
    questions: list[dict] = []
    for path in sorted(CONTENT.rglob("*.json")):
        if track_filter and track_filter not in str(path):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        # Hay ficheros con lista suelta y con {"questions": [...]}: `.get` sobre
        # una lista revienta (como ya documenta check_question_bank.py).
        questions.extend(data if isinstance(data, list) else data.get("questions", []))
    return questions


def fetch(url: str) -> tuple[bool, str]:
    """HEAD first, then GET: some doc sites answer 403 to HEAD but 200 to GET."""
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
                if 200 <= res.status < 300:
                    return True, f"{res.status} ({method})"
        except urllib.error.HTTPError as err:
            if method == "GET":
                return False, f"HTTP {err.code}"
        except Exception as err:  # noqa: BLE001 - any transport failure is a finding
            if method == "GET":
                return False, f"{type(err).__name__}: {err}"
    return False, "no successful response"


def main() -> int:
    track_filter = sys.argv[1] if len(sys.argv) > 1 else None
    questions = load_questions(track_filter)
    if not questions:
        print(f"no questions found{f' for {track_filter}' if track_filter else ''}")
        return 1

    # One fetch per distinct URL, not per question: dozens of questions share a page.
    urls: dict[str, set[str]] = defaultdict(set)
    unverifiable = 0
    for q in questions:
        source = q.get("source") or ""
        found = URL_RE.findall(source)
        if not found:
            unverifiable += 1
            continue
        for url in found:
            urls[url.rstrip(".,;")].add(q["id"])

    print(f"\n{len(questions)} questions, {len(urls)} distinct URLs to check")
    if unverifiable:
        print(
            f"{unverifiable} questions cite a non-URL source (book, PEP, paper) - "
            "not checkable here; they need human sampling"
        )
    print()

    failures = []
    for url in sorted(urls):
        ok, detail = fetch(url)
        print(f"  {'OK  ' if ok else 'FAIL'}  {detail:<18} {url}")
        if not ok:
            failures.append((url, detail, sorted(urls[url])))

    if failures:
        print(f"\n{len(failures)} cited URL(s) did not resolve:\n")
        for url, detail, ids in failures:
            shown = ", ".join(ids[:5]) + (f" (+{len(ids) - 5} more)" if len(ids) > 5 else "")
            print(f"  {url}\n    {detail}\n    cited by: {shown}\n")
        print("Red line 2: fix the citation or remove the claim it supports.\n")
        return 1

    print(f"\nPASS - all {len(urls)} cited URLs resolve\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
