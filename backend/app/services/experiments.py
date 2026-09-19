import hashlib
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.experiment import Experiment, ExperimentAssignment


async def get_user_variant(
    db: Session, experiment_id: UUID, user_id: UUID
) -> str:
    """Get stable variant assignment for user in experiment.
    
    Uses deterministic hash of (experiment_id, user_id) to ensure
    same user always sees same variant.
    """
    existing = db.query(ExperimentAssignment).filter(
        ExperimentAssignment.experiment_id == experiment_id,
        ExperimentAssignment.user_id == user_id
    ).first()
    
    if existing:
        return existing.variant
    
    hash_input = f"{experiment_id}:{user_id}"
    hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
    variant = "A" if hash_value % 2 == 0 else "B"
    
    assignment = ExperimentAssignment(
        experiment_id=experiment_id,
        user_id=user_id,
        variant=variant
    )
    db.add(assignment)
    db.commit()
    return variant


async def get_active_experiments(db: Session) -> list[Experiment]:
    """Get all active experiments."""
    from datetime import datetime
    return db.query(Experiment).filter(
        Experiment.status == "active",
        Experiment.started_at <= datetime.now(),
        (Experiment.ended_at.is_(None) | (Experiment.ended_at > datetime.now()))
    ).all()


async def get_user_experiment_flags(
    db: Session, user_id: UUID
) -> dict[str, str]:
    """Get variant for each active experiment for a user.
    
    Returns: {"experiment_name": "A" | "B"}
    """
    experiments = await get_active_experiments(db)
    flags = {}
    
    for exp in experiments:
        variant = await get_user_variant(db, exp.id, user_id)
        flags[exp.name] = variant
    
    return flags
