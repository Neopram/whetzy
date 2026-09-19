"""Asignacion estable de variantes para los experimentos A/B (24.14).

Estaba escrito contra el SQLAlchemy sincrono (`db.query(...)`) sobre la sesion
async de esta app, asi que cualquier llamada moria con
`'AsyncSession' object has no attribute 'query'`. Nunca se ejecuto: el modelo
tampoco importaba y el router no estaba registrado.
"""

import hashlib
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experiment import Experiment, ExperimentAssignment


async def get_user_variant(
    db: AsyncSession, experiment_id: UUID, user_id: UUID
) -> str:
    """Devuelve la variante de un usuario, creandola la primera vez.

    El reparto sale de un hash de (experimento, usuario) y no de un sorteo: el
    mismo usuario cae siempre del mismo lado aunque se pierda la fila, y dos
    procesos que asignen a la vez coinciden. Con `random` la asignacion
    dependeria de quien pregunte primero y las metricas no se podrian comparar.
    """
    existing = await db.scalar(
        select(ExperimentAssignment).where(
            ExperimentAssignment.experiment_id == experiment_id,
            ExperimentAssignment.user_id == user_id,
        )
    )
    if existing is not None:
        return existing.variant

    digest = hashlib.md5(
        f"{experiment_id}:{user_id}".encode(), usedforsecurity=False
    ).hexdigest()
    variant = "A" if int(digest, 16) % 2 == 0 else "B"

    db.add(
        ExperimentAssignment(
            experiment_id=experiment_id, user_id=user_id, variant=variant
        )
    )
    # flush y no commit: quien llama decide cuando cierra la transaccion, que es
    # como trabaja el resto de servicios. Un commit aqui dentro, en el bucle de
    # `get_user_experiment_flags`, dejaria media asignacion escrita si el
    # siguiente experimento falla.
    await db.flush()
    return variant


async def get_active_experiments(db: AsyncSession) -> list[Experiment]:
    """Experimentos en marcha ahora mismo."""
    now = datetime.now(timezone.utc)
    result = await db.scalars(
        select(Experiment).where(
            Experiment.status == "active",
            Experiment.started_at <= now,
            or_(Experiment.ended_at.is_(None), Experiment.ended_at > now),
        )
    )
    return list(result)


async def get_user_experiment_flags(db: AsyncSession, user_id: UUID) -> dict[str, str]:
    """`{"nombre_del_experimento": "A" | "B"}` para todos los activos."""
    return {
        exp.name: await get_user_variant(db, exp.id, user_id)
        for exp in await get_active_experiments(db)
    }
