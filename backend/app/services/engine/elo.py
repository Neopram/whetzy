"""Elo Rating System adapted for educational item-difficulty calibration.

Two-sided Elo: users have ability ratings, questions have difficulty ratings.
Dynamic K-factor decays from K_init to K_stable over the first N interactions,
solving the cold-start problem for both new users and new items.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class EloEntity:
    rating: float = 1500.0
    interactions: int = 0
    k_init: float = 64.0
    k_stable: float = 12.0
    k_decay_n: int = 20

    @property
    def k(self) -> float:
        if self.interactions >= self.k_decay_n:
            return self.k_stable
        t = self.interactions / self.k_decay_n
        return self.k_init + (self.k_stable - self.k_init) * t


class EloRating:
    def __init__(
        self,
        default_user_rating: float = 1500.0,
        default_item_rating: float = 1500.0,
        scale: float = 400.0,
    ):
        self.default_user_rating = default_user_rating
        self.default_item_rating = default_item_rating
        self.scale = scale

    def expected_score(self, user_rating: float, item_rating: float) -> float:
        return 1.0 / (1.0 + math.pow(10, (item_rating - user_rating) / self.scale))

    def update(
        self,
        user: EloEntity,
        item: EloEntity,
        correct: bool,
    ) -> tuple[EloEntity, EloEntity, float]:
        expected = self.expected_score(user.rating, item.rating)
        outcome = 1.0 if correct else 0.0
        delta = outcome - expected

        user.rating += user.k * delta
        item.rating -= item.k * delta

        user.interactions += 1
        item.interactions += 1

        return user, item, expected

    def estimate_difficulty_tier(self, item_rating: float) -> str:
        if item_rating < 1200:
            return "easy"
        elif item_rating < 1500:
            return "medium"
        elif item_rating < 1800:
            return "hard"
        return "expert"

    def select_matched_items(
        self,
        user: EloEntity,
        items: list[tuple[str, EloEntity]],
        target_p: float = 0.75,
        n: int = 5,
    ) -> list[tuple[str, EloEntity, float]]:
        """Select items closest to a target success probability for the user."""
        scored = []
        for item_id, item in items:
            p = self.expected_score(user.rating, item.rating)
            distance = abs(p - target_p)
            scored.append((item_id, item, p, distance))
        scored.sort(key=lambda x: x[3])
        return [(s[0], s[1], s[2]) for s in scored[:n]]
