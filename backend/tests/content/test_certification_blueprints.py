"""Pins every certification blueprint to the vendor's own published exam guide.

Why this file exists. A certification blueprint decides two things a candidate
pays us for: how many questions of each domain the timed rehearsal draws, and
what the per-domain report tells them to go study. Every number in ours was
typed by hand from a vendor page nobody ever re-read, and **three of the four
certification tracks were wrong**. Nothing could have caught it: no test looked
at a blueprint, and `check_question_bank.py` counts questions, not weights.

Everything below was verified on 2026-09-16 by fetching the sources, not from
memory. The numbers in this file ARE the vendor's numbers.

  PCEP-30-02  https://pythoninstitute.org/pcep-exam-syllabus  (block table)
              https://pythoninstitute.org/pcep                (exam facts)
  SAA-C03     https://d1.awsstatic.com/training-and-certification/docs-sa-assoc/
              AWS-Certified-Solutions-Architect-Associate_Exam-Guide_C03.pdf
  AIF-C01     https://d1.awsstatic.com/training-and-certification/docs-ai-practitioner/
              AWS-Certified-AI-Practitioner_Exam-Guide.pdf

Already fixed by the commit that added this file:
  * PCEP `exam_duration_minutes` was 45. The vendor says "Exam: 40 minutes,
    NDA/Tutorial: 5 minutes" - 45 is those two added together, and the five are
    not exam time. A rehearsal that hands over 12,5 % more clock than the real
    exam is not "the real format".
  * PCEP `exam_guide_url` pointed at the marketing page, which does not carry
    the block table at all - a citation that did not support its own claim.
  * SAA-C03 `exam_guide_url` returned 403. A dead citation (red line 2).

Still broken, each a strict xfail below carrying its measured consequence. They
are xfail rather than fixed here because fixing them is curriculum surgery
(splitting modules, moving skills, authoring the two missing AIF-C01 domains),
not a metadata edit. See ledger 17.13.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from app.services.content_loader import _content_root

# (domain name as the vendor writes it, weight %)
OFFICIAL_BLOCKS: dict[str, list[tuple[str, int]]] = {
    "track09": [
        ("Computer Programming and Python Fundamentals", 18),
        ("Control Flow - Conditional Blocks and Loops", 29),
        ("Data Collections - Tuples, Dictionaries, Lists, and Strings", 25),
        ("Functions and Exceptions", 28),
    ],
    "track10": [
        ("Design Secure Architectures", 30),
        ("Design Resilient Architectures", 26),
        ("Design High-Performing Architectures", 24),
        ("Design Cost-Optimized Architectures", 20),
    ],
    "track11": [
        ("Fundamentals of AI and ML", 20),
        ("Fundamentals of Generative AI", 24),
        ("Applications of Foundation Models", 28),
        ("Guidelines for Responsible AI", 14),
        ("Security, Compliance, and Governance for AI Solutions", 14),
    ],
}

PCEP_EXAM_FACTS = {
    "code": "PCEP-30-02",
    "exam_question_count": 30,
    "exam_duration_minutes": 40,
    "passing_scaled_score": 700,
    "scaled_score_max": 1000,
}


def _tracks() -> list[dict[str, Any]]:
    payload = json.loads(
        (_content_root() / "curriculum" / "tracks.json").read_text(encoding="utf-8")
    )
    return payload["tracks"] if isinstance(payload, dict) else payload


def _track(track_id: str) -> dict[str, Any]:
    return next(t for t in _tracks() if t["id"] == track_id)


def _weights(track: dict[str, Any]) -> list[int]:
    return [
        m["exam_weight_pct"]
        for m in track.get("modules", [])
        if m.get("exam_weight_pct") is not None
    ]


class TestPcepExamFacts:
    def test_exam_facts_match_the_vendor_page(self) -> None:
        cert = _track("track09")["certification"]
        assert {k: cert.get(k) for k in PCEP_EXAM_FACTS} == PCEP_EXAM_FACTS

    def test_exam_guide_url_points_at_the_page_that_carries_the_weights(self) -> None:
        cert = _track("track09")["certification"]
        assert cert["exam_guide_url"] == "https://pythoninstitute.org/pcep-exam-syllabus"


class TestBlueprintInvariants:
    """Properties a blueprint must hold whatever the vendor's numbers are."""

    def test_cloud_practitioner_weights_sum_to_one_hundred(self) -> None:
        assert sum(_weights(_track("track08"))) == 100

    def test_pcep_weights_sum_to_one_hundred(self) -> None:
        assert sum(_weights(_track("track09"))) == 100

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Ledger 17.13. track10 declares 'Domain 1: Design Secure "
            "Architectures' twice - as '(partial)' at 20 % and again at 30 %. "
            "This is the same defect as the weights summing to 120, seen from "
            "the report's side instead of the allocator's: the candidate gets "
            "two half-sized samples of one domain and no way to tell they are "
            "the same thing. Goes green when the track10 modules are merged."
        ),
    )
    def test_no_track_declares_the_same_exam_domain_twice(self) -> None:
        """A duplicated domain splits one row of the report in two, and the
        candidate reads two half-sized samples of the same thing."""
        offenders: list[str] = []
        for track in _tracks():
            names = [
                m["exam_domain"] for m in track.get("modules", []) if m.get("exam_domain")
            ]
            # "Domain 1: X (partial)" and "Domain 1: X" are the same domain.
            base = [n.replace(" (partial)", "") for n in names]
            dupes = {n for n in base if base.count(n) > 1}
            if dupes:
                offenders.append(f"{track['id']}: {sorted(dupes)}")
        assert offenders == [], f"duplicated exam domains: {offenders}"


class TestKnownBrokenBlueprints:
    """Real defects with measured consequences. Strict xfails: the day one is
    fixed its test goes green and must be moved out of this class."""

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Ledger 17.13. Official PCEP-30-02 has FOUR blocks (18/29/25/28); "
            "this track declares THREE (18/29/53) - block 3 carries its own 25 % "
            "plus block 4's 28 %. Measured on the real allocator: the 30-item "
            "rehearsal draws 16 from Data Collections where the real exam draws "
            "7, and 'Functions and Exceptions' (8 items, joint-largest block) "
            "has no domain at all, so the per-domain report can never name it - "
            "which is the one thing that report exists to do."
        ),
    )
    def test_pcep_matches_the_four_official_blocks(self) -> None:
        assert _weights(_track("track09")) == [w for _n, w in OFFICIAL_BLOCKS["track09"]]

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Ledger 17.13. SAA-C03 has FOUR domains summing to 100 (30/26/24/20). "
            "track10 declares FIVE summing to 120, because 'Domain 1: Design "
            "Secure Architectures' appears twice - once as '(partial)' at 20 % "
            "and once at 30 %. Measured on the real allocator: a 65-question "
            "rehearsal hands out 76, and Domain 1 takes 32 of them (42 %) "
            "against a real 30 %."
        ),
    )
    def test_saa_weights_sum_to_one_hundred(self) -> None:
        assert sum(_weights(_track("track10"))) == 100

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Ledger 17.13. AIF-C01 has FIVE domains (20/24/28/14/14). track11 "
            "declares only the first THREE, summing to 72: 'Guidelines for "
            "Responsible AI' and 'Security, Compliance, and Governance for AI "
            "Solutions' - 28 % of the scored exam - are absent from the bank, "
            "from the rehearsal and from the report. Measured on the real "
            "allocator: an 85-question rehearsal hands out 63. Worth noticing "
            "that the domain we skipped on our own AI certification is the "
            "responsible-AI one."
        ),
    )
    def test_aif_weights_sum_to_one_hundred(self) -> None:
        assert sum(_weights(_track("track11"))) == 100
