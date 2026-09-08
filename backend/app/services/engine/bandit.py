"""Thompson Sampling Multi-Armed Bandit for question selection.

Each candidate question is an "arm" with a Beta(alpha, beta) posterior
representing belief about its learning-reward probability. Thompson
Sampling naturally balances exploration (uncertain items get sampled
via wide posteriors) with exploitation (proven items get picked more
consistently).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional


@dataclass
class Arm:
    arm_id: str
    alpha: float = 1.0    # successes + 1
    beta: float = 1.0     # failures + 1
    total_pulls: int = 0

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    def sample(self) -> float:
        return random.betavariate(self.alpha, self.beta)

    def update(self, reward: float) -> None:
        self.alpha += reward
        self.beta += (1.0 - reward)
        self.total_pulls += 1


class ThompsonBandit:
    def __init__(self):
        self.arms: dict[str, Arm] = {}

    def add_arm(self, arm_id: str, prior_alpha: float = 1.0, prior_beta: float = 1.0) -> Arm:
        arm = Arm(arm_id=arm_id, alpha=prior_alpha, beta=prior_beta)
        self.arms[arm_id] = arm
        return arm

    def select(self, eligible_ids: Optional[list[str]] = None) -> Optional[str]:
        pool = self.arms
        if eligible_ids is not None:
            pool = {k: v for k, v in self.arms.items() if k in eligible_ids}
        if not pool:
            return None

        samples = {arm_id: arm.sample() for arm_id, arm in pool.items()}
        return max(samples, key=samples.get)

    def select_top_n(
        self, n: int, eligible_ids: Optional[list[str]] = None,
    ) -> list[str]:
        pool = self.arms
        if eligible_ids is not None:
            pool = {k: v for k, v in self.arms.items() if k in eligible_ids}
        if not pool:
            return []

        samples = [(arm_id, arm.sample()) for arm_id, arm in pool.items()]
        samples.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in samples[:n]]

    def update(self, arm_id: str, reward: float) -> None:
        if arm_id in self.arms:
            self.arms[arm_id].update(reward)

    def compute_reward(
        self,
        correct: bool,
        response_time_ms: int,
        expected_time_ms: int,
        difficulty_match: float,
    ) -> float:
        """Compute learning reward combining correctness, timing, and difficulty match.

        Returns a value in [0, 1] where:
        - correct + appropriate time + good difficulty match → high reward
        - correct but suspiciously fast (guessing) → reduced reward
        - incorrect but good engagement → small partial reward
        """
        if not correct:
            return 0.1 if response_time_ms > expected_time_ms * 0.3 else 0.0

        time_ratio = response_time_ms / max(1, expected_time_ms)
        if time_ratio < 0.15:
            time_score = 0.2  # too fast = likely guess
        elif time_ratio < 0.5:
            time_score = 0.7
        elif time_ratio < 2.0:
            time_score = 1.0
        else:
            time_score = 0.8  # slow but correct

        diff_score = 1.0 - abs(difficulty_match - 0.75) * 2.0
        diff_score = max(0.3, min(1.0, diff_score))

        return 0.5 * time_score + 0.3 * diff_score + 0.2


class NewVsReviewBandit:
    """Higher-level bandit deciding between new content and review."""

    def __init__(self, new_prior: tuple[float, float] = (2.0, 1.0)):
        self.new_arm = Arm(arm_id="new", alpha=new_prior[0], beta=new_prior[1])
        self.review_arm = Arm(arm_id="review", alpha=1.5, beta=1.0)

    def should_review(self, has_due_reviews: bool, has_new_content: bool) -> bool:
        if has_due_reviews and not has_new_content:
            return True
        if has_new_content and not has_due_reviews:
            return False

        new_sample = self.new_arm.sample()
        review_sample = self.review_arm.sample()
        return review_sample > new_sample

    def update(self, was_review: bool, reward: float) -> None:
        arm = self.review_arm if was_review else self.new_arm
        arm.update(reward)
