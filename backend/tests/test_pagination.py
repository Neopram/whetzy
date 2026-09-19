"""Tests for pagination (Series 22.6)."""

import pytest
from pydantic import ValidationError

from app.core.pagination import PaginatedResponse, PaginationParams


def test_pagination_params_defaults():
    """Verify default pagination parameters."""
    params = PaginationParams()
    assert params.limit == 50
    assert params.offset == 0


def test_pagination_params_custom():
    """Verify custom pagination parameters."""
    params = PaginationParams(limit=20, offset=40)
    assert params.limit == 20
    assert params.offset == 40


def test_pagination_params_max_limit():
    """Verify limit is capped at 100."""
    with pytest.raises(ValidationError):
        PaginationParams(limit=101)


def test_pagination_params_min_limit():
    """Verify limit must be at least 1."""
    with pytest.raises(ValidationError):
        PaginationParams(limit=0)


def test_pagination_params_negative_offset():
    """Verify offset cannot be negative."""
    with pytest.raises(ValidationError):
        PaginationParams(offset=-1)


def test_paginated_response_has_more():
    """Verify has_more property works correctly."""
    # 50 items, 10 returned, 20 offset -> more items available
    response = PaginatedResponse(items=list(range(10)), total=50, limit=10, offset=20)
    assert response.has_more is True

    # 50 items, 10 returned, 40 offset -> no more items
    response = PaginatedResponse(items=list(range(10)), total=50, limit=10, offset=40)
    assert response.has_more is False

    # 50 items, 5 returned (last page), 45 offset -> no more items
    response = PaginatedResponse(items=list(range(5)), total=50, limit=10, offset=45)
    assert response.has_more is False
