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
from typing import Optional


@dataclass
class IRTItem:
    item_id: str
    difficulty: float = 0.0      # b parameter
    discrimination: float = 1.0  # a parameter
    guessing: float = 0.20       # c parameter (for MCQ)
    skill_ids: list[str] = field(default_factory=list)
    exposure_count: int = 0
    max_exposure: int = 50


@dataclass
class PlacementState:
    ability_estimate: float = 0.0
    ability_se: float = 1.0  # standard error
    responses: list[tuple[str, bool]] = field(default_factory=list)
    administered_ids: set[str] = field(default_factory=set)
    skill_estimates: dict[str, float] = field(default_factory=dict)


class PlacementEngine:
    def __init__(
        self,
        items: list[IRTItem],
        min_questions: int = 20,
        max_questions: int = 50,
        se_threshold: float = 0.30,
        skip_threshold: float = 0.70,
        skip_min_questions: int = 30,
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
        """Fisher information for 2PL (ignoring guessing for selection)."""
        p = 1.0 / (1.0 + math.exp(-item.discrimination * (theta - item.difficulty)))
        return item.discrimination ** 2 * p * (1.0 - p)

    def select_next_item(self, state: PlacementState) -> Optional[IRTItem]:
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
        """MLE update of ability estimate via Newton-Raphson."""
        state.responses.append((item.item_id, correct))
        state.administered_ids.add(item.item_id)
        item.exposure_count += 1

        for sid in getattr(item, 'skill_ids', []):
            if sid not in state.skill_estimates:
                state.skill_estimates[sid] = {"correct": 0, "total": 0}
            state.skill_estimates[sid]["total"] += 1
            if correct:
                state.skill_estimates[sid]["correct"] += 1

        theta = state.ability_estimate
        for _ in range(10):
            dl = 0.0
            d2l = 0.0
            for resp_id, resp_correct in state.responses:
                resp_item = self.items[resp_id]
                p = self.probability_correct(theta, resp_item)
                p = max(1e-6, min(1 - 1e-6, p))

                a = resp_item.discrimination
                q_term = (p - resp_item.guessing) / (1.0 - resp_item.guessing)
                q_term = max(1e-6, q_term)

                w = q_term / p
                outcome = 1.0 if resp_correct else 0.0

                dl += a * w * (outcome - p)
                d2l -= a ** 2 * w * ((1.0 - p) * w + (outcome - p) * (w - a * q_term * (1.0 - q_term) / p))

            if abs(d2l) < 1e-10:
                break
            theta -= dl / d2l

        theta = max(-4.0, min(4.0, theta))
        state.ability_estimate = theta

        info_sum = sum(
            self.fisher_information(theta, self.items[rid])
            for rid, _ in state.responses
        )
        state.ability_se = 1.0 / math.sqrt(max(1e-6, info_sum))

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

    def get_placement_result(self, state: PlacementState) -> dict:
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
