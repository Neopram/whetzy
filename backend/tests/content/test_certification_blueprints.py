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

Fixed in ledger 18.1:
  * PCEP split to four blocks (18/29/25/28); mod0904 "Functions and Exceptions" added.
  * SAA-C03 de-duplicated Domain 1. AIF-C01 expanded to five domains.

Fixed in ledger 18.13, because 18.1 got the weights right and the contents
wrong: the domains it declared were module labels, and what sat inside those
modules was not what the label said. See the block comment further down.
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
    """The blueprint weights, from wherever this track keeps them.

    A track that declares `exam_domains` keeps them there (18.13); the older
    shape, where a module doubled as a domain, keeps them on the modules. Both
    are read here so the invariants below hold for either.
    """
    if track.get("exam_domains"):
        return [d["weight_pct"] for d in track["exam_domains"]]
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

    def test_saa_weights_sum_to_one_hundred(self) -> None:
        assert sum(_weights(_track("track10"))) == 100

    def test_aif_weights_sum_to_one_hundred(self) -> None:
        assert sum(_weights(_track("track11"))) == 100

    def test_no_track_declares_the_same_exam_domain_twice(self) -> None:
        """A duplicated domain splits one row of the report in two, and the
        candidate reads two half-sized samples of the same thing."""
        offenders: list[str] = []
        for track in _tracks():
            names = [d["name_en"] for d in track.get("exam_domains", [])] or [
                m["exam_domain"] for m in track.get("modules", []) if m.get("exam_domain")
            ]
            # "Domain 1: X (partial)" and "Domain 1: X" are the same domain.
            base = [n.replace(" (partial)", "") for n in names]
            dupes = {n for n in base if base.count(n) > 1}
            if dupes:
                offenders.append(f"{track['id']}: {sorted(dupes)}")
        assert offenders == [], f"duplicated exam domains: {offenders}"

    def test_pcep_matches_the_four_official_blocks(self) -> None:
        assert _weights(_track("track09")) == [w for _n, w in OFFICIAL_BLOCKS["track09"]]


# ---------------------------------------------------------------------------
# 18.13 — the module axis and the domain axis are not the same axis
# ---------------------------------------------------------------------------
#
# 18.1 made this file green by giving every module an `exam_domain` label whose
# weights summed to 100. It never asked whether the skills inside a module had
# anything to do with the domain the module had just been labelled with, and
# for two tracks out of three they did not:
#
#   * AIF-C01 reported "Guidelines for Responsible AI" (14 % of the exam) out of
#     sk110304, which is AI security and privacy, and "Security, Compliance, and
#     Governance" out of sk110305, which is cost optimisation - while sk110303,
#     the bias-and-fairness skill that IS Domain 4, sat in Domain 3.
#   * SAA-C03 labelled the operations module "Design Cost-Optimized
#     Architectures" (20 %) while it held Well-Architected, CloudFormation and
#     CloudWatch, and left the whole networking module without a domain, so 75
#     questions were invisible to both the rehearsal and the report.
#
# A per-domain report that names the wrong domain is worse than no report: the
# candidate goes and studies the thing they already knew. Red line 1.
#
# The check below is cheap and would have caught all of it: in every vendor
# blueprint here, a task statement is numbered `<domain>.<n>`, so a skill citing
# task statement 5.1 cannot belong to a domain whose declared statements are
# 4.1 and 4.2. Self-consistency, not opinion.

TRACKS_WITH_DECLARED_DOMAINS = ("track10", "track11")


def _declared(track_id: str) -> list[dict[str, Any]]:
    return _track(track_id)["exam_domains"]


def _skills(track_id: str) -> list[dict[str, Any]]:
    return [s for m in _track(track_id).get("modules", []) for s in m.get("skills", [])]


class TestSkillDomainMapping:
    @pytest.mark.parametrize("track_id", TRACKS_WITH_DECLARED_DOMAINS)
    def test_declared_domain_weights_match_the_vendor(self, track_id: str) -> None:
        official = OFFICIAL_BLOCKS[track_id]
        declared = [(d["name_en"], d["weight_pct"]) for d in _declared(track_id)]
        # The vendor writes "Domain 1: Design Secure Architectures"; OFFICIAL_BLOCKS
        # carries the part after the colon, which is the part that can go stale.
        assert [(n.split(": ", 1)[1], w) for n, w in declared] == official

    @pytest.mark.parametrize("track_id", TRACKS_WITH_DECLARED_DOMAINS)
    def test_every_skill_is_mapped_or_excluded_on_purpose(self, track_id: str) -> None:
        ids = {d["id"] for d in _declared(track_id)}
        for skill in _skills(track_id):
            assert "exam_domain" in skill, f"{skill['id']} has no exam_domain key"
            if skill["exam_domain"] is None:
                assert skill.get("exam_domain_excluded_reason"), (
                    f"{skill['id']} is unmapped with no reason - an accident and a "
                    f"deliberate exclusion must not look the same"
                )
            else:
                assert skill["exam_domain"] in ids, (
                    f"{skill['id']} maps to {skill['exam_domain']}, not declared"
                )

    @pytest.mark.parametrize("track_id", TRACKS_WITH_DECLARED_DOMAINS)
    def test_task_statement_belongs_to_the_domain_it_claims(self, track_id: str) -> None:
        """The check that would have caught 18.1's mis-mapping."""
        by_id = {d["id"]: d for d in _declared(track_id)}
        offenders: list[str] = []
        for skill in _skills(track_id):
            domain_id = skill["exam_domain"]
            if domain_id is None:
                continue
            statement = skill["exam_task_statement"]
            allowed = by_id[domain_id]["task_statements"]
            if statement not in allowed:
                offenders.append(
                    f"{skill['id']} cites {statement} but {domain_id} covers {allowed}"
                )
        assert offenders == [], offenders

    @pytest.mark.parametrize("track_id", TRACKS_WITH_DECLARED_DOMAINS)
    def test_no_domain_is_empty(self, track_id: str) -> None:
        """An empty domain scores the BKT prior and reports 10 % readiness in
        something nobody can study, because it has nothing in it."""
        mapped = {s["exam_domain"] for s in _skills(track_id)}
        missing = [d["id"] for d in _declared(track_id) if d["id"] not in mapped]
        assert missing == [], f"{track_id} declares domains with no skills: {missing}"

    @pytest.mark.parametrize("track_id", TRACKS_WITH_DECLARED_DOMAINS)
    def test_a_module_never_doubles_as_a_domain(self, track_id: str) -> None:
        """Two sources of truth is how the labels drifted in the first place."""
        for module in _track(track_id)["modules"]:
            assert "exam_domain" not in module, f"{module['id']} still labels a domain"
            assert "exam_weight_pct" not in module

    @pytest.mark.parametrize("track_id", TRACKS_WITH_DECLARED_DOMAINS)
    def test_every_module_renders(self, track_id: str) -> None:
        """`TracksScreen` builds its sections from `[1, 2, 3]`, so a module at
        level 4 is shipped, loaded, examined - and invisible to the learner.
        18.1 put both new AIF-C01 modules there, i.e. 28 % of that exam."""
        for module in _track(track_id)["modules"]:
            assert 1 <= module.get("level", 1) <= 3, f"{module['id']} is unreachable"


class TestDomainPoolsCanFillTheExam:
    """A weight the bank cannot back is a rehearsal that quietly draws short.

    `_domain_allocation` splits the paper by published weight; if a domain's
    answerable pool is smaller than its share, the sitting is not the exam it
    claims to be. Only questions carrying options in BOTH languages count,
    because that is the filter the draw itself applies (red line 3).
    """

    @pytest.mark.parametrize("track_id", TRACKS_WITH_DECLARED_DOMAINS)
    def test_every_domain_has_enough_answerable_questions(self, track_id: str) -> None:
        from app.services.mock_exam import _domain_allocation

        domain_of_skill = {
            s["id"]: s["exam_domain"] for s in _skills(track_id) if s["exam_domain"]
        }
        pool: dict[str, int] = {d["id"]: 0 for d in _declared(track_id)}
        bank = _content_root() / "questions"
        for path in sorted(bank.rglob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            questions = payload["questions"] if isinstance(payload, dict) else payload
            for question in questions:
                domain_id = domain_of_skill.get(question.get("skill_id", ""))
                if domain_id and question.get("options_es") and question.get("options_en"):
                    pool[domain_id] += 1

        weights = {d["id"]: float(d["weight_pct"]) for d in _declared(track_id)}
        total = _track(track_id)["certification"]["exam_question_count"]
        allocation = _domain_allocation(weights, total)
        short = [
            f"{d}: draw needs {allocation[d]}, bank answers {pool[d]}"
            for d in allocation
            if pool[d] < allocation[d]
        ]
        assert short == [], short
