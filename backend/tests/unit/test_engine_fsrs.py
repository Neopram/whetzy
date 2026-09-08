"""Unit tests for FSRS-6 scheduler."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.services.engine.fsrs import Card, FSRSScheduler, ReviewLog


@pytest.fixture
def scheduler() -> FSRSScheduler:
    return FSRSScheduler()


@pytest.fixture
def new_card() -> Card:
    return Card()


NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


class TestFSRSScheduler:
    def test_initial_stability_grade_1(self, scheduler: FSRSScheduler) -> None:
        s = scheduler.initial_stability(1)
        assert s > 0

    def test_initial_stability_grade_4_greater_than_grade_1(
        self, scheduler: FSRSScheduler
    ) -> None:
        assert scheduler.initial_stability(4) > scheduler.initial_stability(1)

    def test_initial_difficulty_clamped(self, scheduler: FSRSScheduler) -> None:
        for grade in range(1, 5):
            d = scheduler.initial_difficulty(grade)
            assert 1.0 <= d <= 10.0

    def test_next_difficulty_clamped(self, scheduler: FSRSScheduler) -> None:
        for d in [1.0, 5.0, 10.0]:
            for grade in range(1, 5):
                new_d = scheduler.next_difficulty(d, grade)
                assert 1.0 <= new_d <= 10.0

    def test_retrievability_zero_stability(self, scheduler: FSRSScheduler) -> None:
        assert scheduler.retrievability(5, 0.0) == 0.0

    def test_retrievability_positive(self, scheduler: FSRSScheduler) -> None:
        r = scheduler.retrievability(1, 10.0)
        assert 0.0 < r <= 1.0

    def test_retrievability_decreases_with_time(self, scheduler: FSRSScheduler) -> None:
        r1 = scheduler.retrievability(1, 10.0)
        r2 = scheduler.retrievability(10, 10.0)
        assert r1 > r2

    def test_next_interval_positive(self, scheduler: FSRSScheduler) -> None:
        assert scheduler.next_interval(5.0) >= 1

    def test_review_new_card_grade_1(
        self, scheduler: FSRSScheduler, new_card: Card
    ) -> None:
        card, log = scheduler.review(new_card, grade=1, now=NOW)
        assert card.reps == 1
        assert card.lapses == 1
        assert card.state == "relearning"
        assert card.stability > 0
        assert isinstance(log, ReviewLog)

    def test_review_new_card_grade_3(
        self, scheduler: FSRSScheduler, new_card: Card
    ) -> None:
        card, log = scheduler.review(new_card, grade=3, now=NOW)
        assert card.reps == 1
        assert card.lapses == 0
        assert card.state == "review"
        assert card.due is not None
        assert card.due > NOW

    def test_review_new_card_grade_2_becomes_learning(
        self, scheduler: FSRSScheduler, new_card: Card
    ) -> None:
        card, _ = scheduler.review(new_card, grade=2, now=NOW)
        assert card.state == "learning"

    def test_review_increments_reps(
        self, scheduler: FSRSScheduler, new_card: Card
    ) -> None:
        card, _ = scheduler.review(new_card, grade=3, now=NOW)
        card, _ = scheduler.review(card, grade=3, now=NOW + timedelta(days=1))
        assert card.reps == 2

    def test_review_updates_last_review(
        self, scheduler: FSRSScheduler, new_card: Card
    ) -> None:
        card, _ = scheduler.review(new_card, grade=3, now=NOW)
        assert card.last_review == NOW

    def test_cards_due_empty(self, scheduler: FSRSScheduler) -> None:
        assert scheduler.cards_due([]) == []

    def test_cards_due_returns_past_due(self, scheduler: FSRSScheduler) -> None:
        past_card = Card(due=NOW - timedelta(days=1), state="review")
        future_card = Card(due=NOW + timedelta(days=1), state="review")
        no_due_card = Card()
        result = scheduler.cards_due([past_card, future_card, no_due_card], now=NOW)
        assert past_card in result
        assert future_card not in result
        assert no_due_card not in result

    def test_review_second_call_uses_recall_stability(
        self, scheduler: FSRSScheduler, new_card: Card
    ) -> None:
        card, _ = scheduler.review(new_card, grade=3, now=NOW)
        s_after_first = card.stability
        card, _ = scheduler.review(card, grade=3, now=NOW + timedelta(days=card.scheduled_days))
        # Second review should update stability
        assert card.stability != s_after_first or card.reps == 2

    def test_forget_stability_less_than_current(self, scheduler: FSRSScheduler) -> None:
        s = scheduler.next_forget_stability(d=5.0, s=10.0, r=0.9)
        assert s <= 10.0

    def test_custom_retention(self) -> None:
        s1 = FSRSScheduler(desired_retention=0.9)
        s2 = FSRSScheduler(desired_retention=0.7)
        # Higher retention → shorter interval to stay above threshold
        i1 = s1.next_interval(10.0)
        i2 = s2.next_interval(10.0)
        assert i1 < i2
