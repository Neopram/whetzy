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

B.11 (2026-10-04) adds the other half of "sin datos": an EXPLICIT, named
threshold for "ready to sit the simulacro" (`DOMAIN_READY_THRESHOLD`,
previously a bare `0.75` local to the endpoint function) and `is_domain_ready`,
so "ready" always means the same thing everywhere it's checked — including
a domain with no data, which is never ready, not simply unmarked.
"""

from __future__ import annotations

from dataclasses import dataclass

# The bar a domain's mean p_known must clear to count as "ready for the
# simulacro" (B.11). Named and exported rather than a bare literal inside
# the endpoint, so every reader of a "ready" flag can find out what it
# actually means without reading the endpoint's source.
DOMAIN_READY_THRESHOLD = 0.75


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
    `UserSkillState` row for.

    42.6 (PLAN_ULTRACODE §4, hecho en 43.4): la media va sobre TODAS las
    skills del dominio y una sin estado cuenta 0. Antes iba solo sobre las
    evaluadas, así que una skill al 0,9 entre diez dejaba el dominio «listo».
    Un dominio sin ninguna evaluada sigue siendo «sin datos» (None), no 0: la
    cobertura la dice `skills_assessed`."""
    assessed_values = [p_known_by_skill[sid] for sid in skill_ids if sid in p_known_by_skill]
    mean_p = sum(assessed_values) / len(skill_ids) if assessed_values else None
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


def is_domain_ready(mastery: DomainMastery, threshold: float = DOMAIN_READY_THRESHOLD) -> bool:
    """A domain with no data is never ready — "sin datos" and "ready" are
    mutually exclusive by construction, not by a caller remembering to
    check both."""
    return mastery.p_known_mean is not None and mastery.p_known_mean >= threshold


def is_ready_for_simulacro(domains: list[DomainMastery], threshold: float = DOMAIN_READY_THRESHOLD) -> bool:
    """Ready for the simulacro means every domain in the track clears the
    bar — one domain still "sin datos" or below threshold is enough to
    hold the whole track back. A track with no domains at all is never
    "ready" (there is nothing to be ready about)."""
    return bool(domains) and all(is_domain_ready(d, threshold) for d in domains)
