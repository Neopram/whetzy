"""One function for per-domain (exam-area) mastery (C.2, 2026-10-04).

Before this module existed, `get_certification_readiness`
(`app/api/v1/endpoints/exams.py`) computed this inline, and treated a skill
the learner had never touched as `p_known = 0.1` (the BKT prior) when
averaging a domain's mastery — so a domain with ZERO skills attempted
reported a specific-looking `p_known_mean = 0.1` and `ready: false`,
indistinguishable from a domain the learner had actually been tested on and
found wanting. "We have no evidence yet" and "we have evidence and it's
bad" are different claims; conflating them under the same number is exactly
the kind of confident-looking-but-empty claim this product can't afford on
a screen that tells someone whether they're ready for a certification exam.

This module answers two separate questions per domain: do we have ANY
evidence at all (`skills_assessed > 0`), and if so, what does it say
(`p_known_mean`, averaged ONLY over skills actually attempted — never
padded with the BKT prior for the rest). `p_known_mean` is `None` exactly
when there is no evidence ("sin datos"), never a number standing in for
that absence.

Used by `get_certification_readiness` today; the same function is meant to
back a domain-level mastery breakdown on Hoy, Rutas and Estadísticas too
(frontend wiring is S1's — see the NECESITO in the C.2 PR for the contract).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainMastery:
    domain_id: str
    weight_pct: float
    p_known_mean: float | None  # None == sin datos: no skill in this domain has been attempted
    skills_assessed: int
    skills_total: int

    @property
    def has_data(self) -> bool:
        return self.skills_assessed > 0


def compute_domain_mastery(
    domain_id: str,
    weight_pct: float,
    skill_ids: list[str],
    p_known_by_skill: dict[str, float],
) -> DomainMastery:
    """`skill_ids` is every skill in the domain (for `skills_total`);
    `p_known_by_skill` holds only skills the learner actually has a
    `UserSkillState` row for — a skill missing from it is "never attempted",
    not "attempted and scored 0"."""
    assessed_values = [p_known_by_skill[sid] for sid in skill_ids if sid in p_known_by_skill]
    mean_p = sum(assessed_values) / len(assessed_values) if assessed_values else None
    return DomainMastery(
        domain_id=domain_id,
        weight_pct=weight_pct,
        p_known_mean=round(mean_p, 4) if mean_p is not None else None,
        skills_assessed=len(assessed_values),
        skills_total=len(skill_ids),
    )


def compute_weighted_overall_mastery(domains: list[DomainMastery]) -> float | None:
    """Weighted average across domains that HAVE data. A domain with no
    data contributes to neither the numerator nor the denominator — it is
    left out of the average entirely, rather than silently pulled toward a
    specific value (0.1 or otherwise) as if it had been measured. Returns
    `None` (sin datos) only when NO domain has any evidence at all."""
    weighted_sum = 0.0
    total_weight = 0.0
    for domain in domains:
        if domain.p_known_mean is None:
            continue
        weighted_sum += domain.p_known_mean * domain.weight_pct
        total_weight += domain.weight_pct
    if total_weight == 0:
        return None
    return round(weighted_sum / total_weight, 4)
