"""Computer Adaptive Testing (CAT) for placement exams.

Uses 2PL IRT with Thompson-Sampled item selection (BanditCAT approach).
Dynamically selects questions to maximize information about the test-taker's
ability, converging on a reliable estimate in ~20-30 questions.

For module skip: requires 70% weighted accuracy on 300+ question pool
to bypass a module entirely (Duolingo-style placement).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IRTItem:
    item_id: str
    difficulty: float = 0.0      # b parameter
    discrimination: float = 1.0  # a parameter
    guessing: float = 0.20       # c parameter (for MCQ)
    skill_ids: list[str] = field(default_factory=list)
    exposure_count: int = 0
    max_exposure: int = 50


#: Rejilla de theta para la estimacion EAP: de -4 a 4 en pasos de 0,05, el
#: mismo rango al que antes se recortaba el resultado de Newton.
THETA_GRID: tuple[float, ...] = tuple(-4.0 + 0.05 * i for i in range(161))


def _log_prior(theta: float) -> float:
    """Normal(0, 1) en logits: la poblacion de partida, sin la constante."""
    return -0.5 * theta * theta


@dataclass
class PlacementState:
    ability_estimate: float = 0.0
    ability_se: float = 1.0  # desviacion tipica a posteriori
    responses: list[tuple[str, bool]] = field(default_factory=list)
    administered_ids: set[str] = field(default_factory=set)
    skill_estimates: dict[str, dict[str, int]] = field(default_factory=dict)
    #: Log-posterior de theta sobre `THETA_GRID`. Cada respuesta suma su
    #: termino, asi que actualizar cuesta lo mismo con 1 que con 50.
    log_posterior: list[float] = field(
        default_factory=lambda: [_log_prior(t) for t in THETA_GRID]
    )


class PlacementEngine:
    def __init__(
        self,
        items: list[IRTItem],
        min_questions: int = 20,
        max_questions: int = 50,
        se_threshold: float = 0.30,
        skip_threshold: float = 0.70,
        # Preguntas de un MISMO modulo antes de poder recomendar saltarlo.
        # Valia 30, y con `max_questions=50` repartidas entre los 12 modulos
        # de un track ningun modulo llega: medido en produccion (maximo 7) y
        # simulado con el banco real en cinco niveles de habilidad (media 7,6
        # a 9,4; pico 11). Es decir, «saltate lo que ya dominas» —la razon de
        # que exista la prueba— no podia dispararse nunca. Ocho si se alcanza
        # y mantiene la exigencia: con `skip_threshold=0.70` hacen falta 6
        # aciertos de 8 en ese modulo.
        skip_min_questions: int = 8,
    ):
        self.items = {item.item_id: item for item in items}
        self.item_list = items
        self.min_questions = min_questions
        self.max_questions = max_questions
        self.se_threshold = se_threshold
        self.skip_threshold = skip_threshold
        self.skip_min_questions = skip_min_questions

    def probability_correct(self, theta: float, item: IRTItem) -> float:
        """3PL IRT probability."""
        exponent = -item.discrimination * (theta - item.difficulty)
        exponent = max(-20.0, min(20.0, exponent))
        return item.guessing + (1.0 - item.guessing) / (1.0 + math.exp(exponent))

    def fisher_information(self, theta: float, item: IRTItem) -> float:
        """Fisher information for 2PL (ignoring guessing for selection).

        Same exponent clamp as `probability_correct` just above — without
        it, a large discrimination far from theta raises `OverflowError`
        from `math.exp`. Reachable in production: `select_next_item`'s
        Thompson sampling draws `discrimination` from an unbounded gamma,
        and `update_ability`'s Newton-Raphson can itself walk an item's
        *ability* estimate far from where its responses actually sit before
        it converges. Found calibrating item parameters offline (14.10) with
        simulated data sparse enough to produce a transient extreme
        discrimination estimate — the same shape of input `select_next_item`
        can hand this method live.
        """
        exponent = -item.discrimination * (theta - item.difficulty)
        exponent = max(-20.0, min(20.0, exponent))
        p = 1.0 / (1.0 + math.exp(exponent))
        return item.discrimination ** 2 * p * (1.0 - p)

    def select_next_item(self, state: PlacementState) -> IRTItem | None:
        """BanditCAT-style item selection with Thompson Sampling."""
        available = [
            item for item in self.item_list
            if item.item_id not in state.administered_ids
            and item.exposure_count < item.max_exposure
        ]
        if not available:
            return None

        scored = []
        for item in available:
            sampled_a = max(0.1, random.gammavariate(
                item.discrimination / 0.3, 0.3,
            ))
            sampled_item = IRTItem(
                item_id=item.item_id,
                difficulty=item.difficulty,
                discrimination=sampled_a,
                guessing=item.guessing,
            )
            info = self.fisher_information(state.ability_estimate, sampled_item)
            scored.append((item, info))

        scored.sort(key=lambda x: x[1], reverse=True)

        top_k = min(5, len(scored))
        weights = [s[1] for s in scored[:top_k]]
        total = sum(weights)
        if total <= 0:
            return scored[0][0]

        r = random.random() * total
        cumulative = 0.0
        for item, w in scored[:top_k]:
            cumulative += w
            if r <= cumulative:
                return item
        return scored[0][0]

    def update_ability(self, state: PlacementState, item: IRTItem, correct: bool) -> None:
        """Estimacion EAP (media a posteriori) con prior Normal(0, 1).

        Antes era Newton-Raphson de maxima verosimilitud sin proteccion: con 12
        aciertos de 50 —el azar con cuatro opciones— divergia y daba theta = +4
        («Avanzado») tanto con dificultades sembradas por nivel como con todas
        iguales (2026-10-16, `tests/unit/test_placement_theta.py`). La EAP no
        puede divergir, siempre devuelve un valor dentro de la rejilla, sube con
        cada acierto y baja con cada fallo, y con pocas respuestas se queda
        cerca del centro en vez de saltar a un extremo. `ability_se` es la
        desviacion tipica a posteriori, que es lo que mira `should_stop`.
        """
        state.responses.append((item.item_id, correct))
        state.administered_ids.add(item.item_id)
        item.exposure_count += 1

        for sid in getattr(item, 'skill_ids', []):
            if sid not in state.skill_estimates:
                state.skill_estimates[sid] = {"correct": 0, "total": 0}
            state.skill_estimates[sid]["total"] += 1
            if correct:
                state.skill_estimates[sid]["correct"] += 1

        for j, theta in enumerate(THETA_GRID):
            p = min(1.0 - 1e-9, max(1e-9, self.probability_correct(theta, item)))
            state.log_posterior[j] += math.log(p if correct else 1.0 - p)

        top = max(state.log_posterior)
        weights = [math.exp(lp - top) for lp in state.log_posterior]
        total = sum(weights)
        mean = sum(t * w for t, w in zip(THETA_GRID, weights, strict=True)) / total
        variance = sum((t - mean) ** 2 * w for t, w in zip(THETA_GRID, weights, strict=True)) / total
        state.ability_estimate = mean
        state.ability_se = math.sqrt(max(variance, 1e-12))

    def should_stop(self, state: PlacementState) -> bool:
        n = len(state.responses)
        if n < self.min_questions:
            return False
        if n >= self.max_questions:
            return True
        return state.ability_se <= self.se_threshold

    def can_skip_module(self, state: PlacementState, module_skill_ids: list[str]) -> bool:
        """Check if the test-taker demonstrated enough mastery to skip a module."""
        relevant = [
            state.skill_estimates[sid]
            for sid in module_skill_ids
            if sid in state.skill_estimates
        ]
        if not relevant:
            return False

        total_correct = sum(r["correct"] for r in relevant)
        total_questions = sum(r["total"] for r in relevant)

        if total_questions < self.skip_min_questions:
            return False

        return (total_correct / total_questions) >= self.skip_threshold

    def get_placement_result(self, state: PlacementState) -> dict[str, Any]:
        total = len(state.responses)
        correct = sum(1 for _, c in state.responses if c)

        skill_mastery = {}
        for sid, data in state.skill_estimates.items():
            if data["total"] > 0:
                skill_mastery[sid] = round(data["correct"] / data["total"], 3)

        return {
            "ability_estimate": round(state.ability_estimate, 3),
            "ability_se": round(state.ability_se, 3),
            "total_questions": total,
            "correct": correct,
            "accuracy": round(correct / max(1, total), 3),
            "skill_mastery": skill_mastery,
            "reliability": round(1.0 - state.ability_se ** 2, 3) if state.ability_se < 1.0 else 0.0,
        }
