"""Qué hace cada fuente de evidencia con el dominio de una skill (42.9, ADR-63 §3-4).

Una respuesta mueve `p_known` por BKT venga de donde venga; lo que cambia según
la fuente es si puede llevarla hasta «dominada» y si cuenta para la puerta de
evidencia (`MIN_EVIDENCE_ANSWERS` respuestas de práctica). Un duelo o un
test-out son evidencia real, pero no sustituyen a practicar: sin este tope,
veinte aciertos de duelo marcaban una skill como dominada sin una sola
respuesta de práctica.

La prueba de nivel no pasa por aquí (siembra por módulo, ADR-65 D4, con su
propio techo de 0,6), pero figura en la tabla porque tampoco cuenta para la
puerta: suma `attempts`, no `practice_attempts`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.config import settings

EvidenceSource = Literal["practice", "duel", "test_out", "placement"]

NON_PRACTICE_CAP: float = settings.NON_PRACTICE_MASTERY_CAP


@dataclass(frozen=True)
class EvidenceRule:
    counts_for_gate: bool
    # Una fuente con tope no sube `p_known` por encima de él por sí sola; si la
    # práctica ya lo dejó más alto, ni lo sube más ni lo baja por acertar.
    cap: float | None
    # El test-out aprobado nunca baja el dominio (S.9, `quiz.apply_exam_evidence`).
    floor_at_before: bool


RULES: dict[str, EvidenceRule] = {
    "practice": EvidenceRule(counts_for_gate=True, cap=None, floor_at_before=False),
    "duel": EvidenceRule(counts_for_gate=False, cap=NON_PRACTICE_CAP, floor_at_before=False),
    "test_out": EvidenceRule(counts_for_gate=False, cap=NON_PRACTICE_CAP, floor_at_before=True),
    "placement": EvidenceRule(counts_for_gate=False, cap=NON_PRACTICE_CAP, floor_at_before=True),
}


def bound(source: str, before: float, after: float) -> float:
    """`p_known` tras aplicar la regla de `source` al resultado de BKT."""
    rule = RULES[source]
    value = after
    if rule.cap is not None:
        value = min(value, max(before, rule.cap))
    if rule.floor_at_before:
        value = max(value, before)
    return value
