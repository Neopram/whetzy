"""Unit tests for Elo Rating engine."""

from __future__ import annotations

import pytest

from app.services.engine.elo import EloEntity, EloRating


@pytest.fixture
def elo() -> EloRating:
    return EloRating()


@pytest.fixture
def user_entity() -> EloEntity:
    return EloEntity(rating=1500.0, interactions=0)


@pytest.fixture
def item_entity() -> EloEntity:
    return EloEntity(rating=1500.0, interactions=0)


class TestEloEntity:
    def test_k_at_zero_interactions(self) -> None:
        e = EloEntity(k_init=64.0, k_stable=12.0, k_decay_n=20)
        assert e.k == pytest.approx(64.0)

    def test_k_at_full_interactions(self) -> None:
        e = EloEntity(interactions=20, k_init=64.0, k_stable=12.0, k_decay_n=20)
        assert e.k == pytest.approx(12.0)

    def test_k_linear_decay(self) -> None:
        e = EloEntity(interactions=10, k_init=64.0, k_stable=12.0, k_decay_n=20)
        expected = 64.0 + (12.0 - 64.0) * (10 / 20)
        assert e.k == pytest.approx(expected)


class TestEloRating:
    def test_expected_score_equal_ratings(self, elo: EloRating) -> None:
        assert elo.expected_score(1500.0, 1500.0) == pytest.approx(0.5)

    def test_expected_score_user_stronger(self, elo: EloRating) -> None:
        assert elo.expected_score(1700.0, 1500.0) > 0.5

    def test_expected_score_user_weaker(self, elo: EloRating) -> None:
        assert elo.expected_score(1300.0, 1500.0) < 0.5

    def test_update_correct_raises_user_rating(
        self, elo: EloRating, user_entity: EloEntity, item_entity: EloEntity
    ) -> None:
        r_before = user_entity.rating
        elo.update(user_entity, item_entity, correct=True)
        assert user_entity.rating > r_before

    def test_update_wrong_lowers_user_rating(
        self, elo: EloRating, user_entity: EloEntity, item_entity: EloEntity
    ) -> None:
        r_before = user_entity.rating
        elo.update(user_entity, item_entity, correct=False)
        assert user_entity.rating < r_before

    def test_update_correct_lowers_item_rating(
        self, elo: EloRating, user_entity: EloEntity, item_entity: EloEntity
    ) -> None:
        r_before = item_entity.rating
        elo.update(user_entity, item_entity, correct=True)
        assert item_entity.rating < r_before

    def test_update_wrong_raises_item_rating(
        self, elo: EloRating, user_entity: EloEntity, item_entity: EloEntity
    ) -> None:
        r_before = item_entity.rating
        elo.update(user_entity, item_entity, correct=False)
        assert item_entity.rating > r_before

    def test_update_increments_interactions(
        self, elo: EloRating, user_entity: EloEntity, item_entity: EloEntity
    ) -> None:
        elo.update(user_entity, item_entity, correct=True)
        assert user_entity.interactions == 1
        assert item_entity.interactions == 1

    def test_estimate_difficulty_tier_easy(self, elo: EloRating) -> None:
        assert elo.estimate_difficulty_tier(1100.0) == "easy"

    def test_estimate_difficulty_tier_medium(self, elo: EloRating) -> None:
        assert elo.estimate_difficulty_tier(1350.0) == "medium"

    def test_estimate_difficulty_tier_hard(self, elo: EloRating) -> None:
        assert elo.estimate_difficulty_tier(1650.0) == "hard"

    def test_estimate_difficulty_tier_expert(self, elo: EloRating) -> None:
        assert elo.estimate_difficulty_tier(1900.0) == "expert"

    def test_select_matched_items_empty(self, elo: EloRating, user_entity: EloEntity) -> None:
        result = elo.select_matched_items(user_entity, [], n=5)
        assert result == []

    def test_select_matched_items_returns_n(self, elo: EloRating, user_entity: EloEntity) -> None:
        items = [(f"q{i}", EloEntity(rating=1500.0 + i * 50)) for i in range(10)]
        result = elo.select_matched_items(user_entity, items, target_p=0.75, n=3)
        assert len(result) == 3

    def test_select_matched_items_closest_to_target(
        self, elo: EloRating, user_entity: EloEntity
    ) -> None:
        user_entity.rating = 1500.0
        # At 0.75 prob the item rating should be lower (easier) than user
        items = [
            ("easy_item", EloEntity(rating=1200.0)),
            ("matched_item", EloEntity(rating=1300.0)),  # closer to 0.75 for 1500 user
            ("hard_item", EloEntity(rating=1800.0)),
        ]
        result = elo.select_matched_items(user_entity, items, target_p=0.75, n=1)
        # The closest to p=0.75 should be selected first
        assert len(result) == 1
        selected_id = result[0][0]
        assert selected_id in {"easy_item", "matched_item"}

    def test_expected_returns_third_value(
        self, elo: EloRating, user_entity: EloEntity, item_entity: EloEntity
    ) -> None:
        _, _, expected = elo.update(user_entity, item_entity, correct=True)
        assert 0.0 <= expected <= 1.0
