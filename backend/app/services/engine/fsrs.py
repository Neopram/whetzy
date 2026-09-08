"""FSRS-6 (Free Spaced Repetition Scheduler) — 21-parameter DSR model.

Implements the full Difficulty-Stability-Retrievability model from
open-spaced-repetition. Trained on ~700M Anki reviews; needs 20-30%
fewer reviews than SM-2 for equal retention.

Grades: 1=Again, 2=Hard, 3=Good, 4=Easy
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


DEFAULTS: list[float] = [
    0.40255, 1.18385, 3.173, 15.69105,      # w0-w3: initial stability per grade
    7.1949, 0.5345, 1.4604, 0.0046,          # w4-w7: difficulty params
    1.54575, 0.1192, 1.01925, 1.9395,        # w8-w11: recall stability update
    0.11, 0.29605, 2.2698,                   # w12-w14: lapse stability update
    0.2315, 2.9898,                          # w15-w16: hard penalty, easy bonus
    0.51655, 0.6621,                         # w17-w18: short-term stability
    0.0, 0.0,                                # w19-w20: reserved
]


@dataclass
class Card:
    stability: float = 0.0
    difficulty: float = 0.0
    elapsed_days: int = 0
    scheduled_days: int = 0
    reps: int = 0
    lapses: int = 0
    state: str = "new"  # new | learning | review | relearning
    due: Optional[datetime] = None
    last_review: Optional[datetime] = None


@dataclass
class ReviewLog:
    card_id: str
    grade: int
    elapsed_days: int
    scheduled_days: int
    review_time: datetime
    stability: float
    difficulty: float
    retrievability: float


class FSRSScheduler:
    def __init__(
        self,
        params: Optional[list[float]] = None,
        desired_retention: float = 0.9,
    ):
        self.w = list(params or DEFAULTS)
        assert len(self.w) >= 17
        while len(self.w) < 21:
            self.w.append(0.0)
        self.desired_retention = desired_retention

    def _clamp(self, v: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, v))

    def retrievability(self, elapsed_days: int, stability: float) -> float:
        if stability <= 0:
            return 0.0
        w20 = self.w[20] if abs(self.w[20]) > 1e-9 else 1.0
        factor = pow(0.9, -1.0 / w20) - 1.0
        return pow(1.0 + factor * elapsed_days / stability, -w20)  # type: ignore[no-any-return]

    def initial_stability(self, grade: int) -> float:
        return max(0.01, self.w[grade - 1])

    def initial_difficulty(self, grade: int) -> float:
        return self._clamp(
            self.w[4] - math.exp(self.w[5] * (grade - 1)) + 1,
            1.0, 10.0,
        )

    def next_difficulty(self, d: float, grade: int) -> float:
        delta = -self.w[6] * (grade - 3)
        d_prime = d + delta * (10.0 - d) / 9.0
        d_out = self.w[7] * self.initial_difficulty(4) + (1 - self.w[7]) * d_prime
        return self._clamp(d_out, 1.0, 10.0)

    def next_recall_stability(
        self, d: float, s: float, r: float, grade: int,
    ) -> float:
        hard_penalty = self.w[15] if grade == 2 else 1.0
        easy_bonus = self.w[16] if grade == 4 else 1.0
        return s * (  # type: ignore[no-any-return]
            1.0
            + math.exp(self.w[8])
            * (11.0 - d)
            * pow(s, -self.w[9])
            * (math.exp(self.w[10] * (1.0 - r)) - 1.0)
            * hard_penalty
            * easy_bonus
        )

    def next_forget_stability(
        self, d: float, s: float, r: float,
    ) -> float:
        new_s = (
            self.w[11]
            * pow(d, -self.w[12])
            * (pow(s + 1.0, self.w[13]) - 1.0)
            * math.exp(self.w[14] * (1.0 - r))
        )
        return min(new_s, s)  # type: ignore[no-any-return]

    def next_interval(self, stability: float) -> int:
        w20 = self.w[20] if abs(self.w[20]) > 1e-9 else 1.0
        factor = pow(0.9, -1.0 / w20) - 1.0
        if factor <= 0:
            return max(1, round(stability * 0.9))
        interval = (stability / factor) * (
            pow(self.desired_retention, -1.0 / w20) - 1.0
        )
        return max(1, round(interval))  # type: ignore[no-any-return]

    def review(
        self, card: Card, grade: int, now: Optional[datetime] = None,
    ) -> tuple[Card, ReviewLog]:
        now = now or datetime.utcnow()
        elapsed = 0
        if card.last_review:
            elapsed = max(0, (now - card.last_review).days)

        r = self.retrievability(elapsed, card.stability) if card.reps > 0 else 0.0

        if card.state == "new" or card.reps == 0:
            new_s = self.initial_stability(grade)
            new_d = self.initial_difficulty(grade)
        else:
            new_d = self.next_difficulty(card.difficulty, grade)
            if grade == 1:
                new_s = self.next_forget_stability(card.difficulty, card.stability, r)
            else:
                new_s = self.next_recall_stability(card.difficulty, card.stability, r, grade)

        interval = self.next_interval(new_s)

        log = ReviewLog(
            card_id="",
            grade=grade,
            elapsed_days=elapsed,
            scheduled_days=card.scheduled_days,
            review_time=now,
            stability=new_s,
            difficulty=new_d,
            retrievability=r,
        )

        card.stability = new_s
        card.difficulty = new_d
        card.elapsed_days = elapsed
        card.scheduled_days = interval
        card.reps += 1
        card.last_review = now
        card.due = now + timedelta(days=interval)

        if grade == 1:
            card.lapses += 1
            card.state = "relearning"
        elif card.state in ("new", "learning"):
            card.state = "learning" if grade == 2 else "review"
        else:
            card.state = "review"

        return card, log

    def cards_due(
        self, cards: list[Card], now: Optional[datetime] = None,
    ) -> list[Card]:
        now = now or datetime.utcnow()
        return [c for c in cards if c.due and c.due <= now]
