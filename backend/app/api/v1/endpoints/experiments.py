import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.experiments import get_user_experiment_flags

logger = logging.getLogger("whetzy.experiments")

router = APIRouter(tags=["experiments"])


@router.get("/flags")
async def get_experiment_flags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict[str, dict[str, str]]:
    """Get A/B variant assignments for current user."""
    try:
        flags = await get_user_experiment_flags(db, current_user.id)
        return {"flags": flags}
    except Exception:
        # Unas flags rotas no pueden tumbar la app, asi que se degrada a
        # "sin experimentos". Pero SIN log esto devolvia 200 y silencio:
        # una caida de BD parecia "este usuario no esta en ningun
        # experimento" y no habia forma de distinguirlas.
        logger.exception("no pude resolver las flags de %s", current_user.id)
        return {"flags": {}}
