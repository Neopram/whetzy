from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.services.experiments import get_user_experiment_flags

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("/flags")
async def get_experiment_flags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get A/B variant assignments for current user."""
    try:
        flags = await get_user_experiment_flags(db, current_user.id)
        return {"flags": flags}
    except Exception:
        return {"flags": {}}
