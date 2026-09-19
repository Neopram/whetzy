"""Pagination helpers for list endpoints.

Series 22.6: LIMIT/OFFSET pagination on all list endpoints (default limit=50, max=100).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Query parameters for pagination."""

    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Number of items to return (max 100)",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of items to skip",
    )


class PaginatedResponse(BaseModel):
    """Response wrapper for paginated lists."""

    items: list[Any]
    total: int
    limit: int
    offset: int

    class Config:
        arbitrary_types_allowed = True

    @property
    def has_more(self) -> bool:
        """Check if there are more items available."""
        return self.offset + len(self.items) < self.total
