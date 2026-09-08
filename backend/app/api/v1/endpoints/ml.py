"""ML management endpoints — model registry info and rollback."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.ml.registry import registry
from app.models.user import User

router = APIRouter()


@router.get("/version", summary="Active DKT checkpoint version")
async def get_ml_version(
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Return info about the currently loaded DKT model checkpoint."""
    return registry.current_info()


@router.post("/rollback", summary="Roll back to a previous DKT checkpoint")
async def rollback_model(
    version: int,
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Load a specific DKT checkpoint version (replaces the active model)."""
    available = registry.list_versions()
    if not available:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No DKT checkpoints found.",
        )
    if version not in available:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version v{version} not found. Available: {available}",
        )
    await registry.rollback(version)
    return registry.current_info()
