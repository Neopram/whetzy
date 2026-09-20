"""Asignacion de variantes A/B (24.14).

Estaban escritos contra el SQLAlchemy sincrono y sin `await`, asi que las
aserciones comparaban dos objetos corrutina entre si —cosa que siempre falla—
y ninguna llegaba a tocar el servicio.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experiment import Experiment, ExperimentAssignment
from app.services.experiments import get_active_experiments, get_user_variant


@pytest_asyncio.fixture
async def experiment(db_session: AsyncSession) -> Experiment:
    exp = Experiment(
        name="test_cta_landing",
        description="CTA button color test",
        variant_a_label="Blue",
        variant_b_label="Green",
        hypothesis="Green CTA increases signups by 5%",
        status="active",
        started_at=datetime.now(UTC),
    )
    db_session.add(exp)
    await db_session.flush()
    return exp


@pytest.mark.asyncio
async def test_deterministic_variant_assignment(
    db_session: AsyncSession, experiment: Experiment
) -> None:
    """El mismo usuario cae siempre en la misma variante."""
    user_id = uuid4()

    first = await get_user_variant(db_session, experiment.id, user_id)
    second = await get_user_variant(db_session, experiment.id, user_id)

    assert first == second
    assert first in ("A", "B")


@pytest.mark.asyncio
async def test_variant_assignment_is_not_random(
    db_session: AsyncSession, experiment: Experiment
) -> None:
    """Sin fila guardada, el reparto se recalcula igual.

    Es lo que separa un hash de un sorteo: si se pierde la asignacion, el
    usuario vuelve a la misma variante y la metrica sigue siendo comparable.
    """
    user_id = uuid4()
    variant = await get_user_variant(db_session, experiment.id, user_id)

    stored = await db_session.scalar(
        select(ExperimentAssignment).where(
            ExperimentAssignment.experiment_id == experiment.id,
            ExperimentAssignment.user_id == user_id,
        )
    )
    await db_session.delete(stored)
    await db_session.flush()

    assert await get_user_variant(db_session, experiment.id, user_id) == variant


@pytest.mark.asyncio
async def test_variant_distribution(
    db_session: AsyncSession, experiment: Experiment
) -> None:
    """Con 100 usuarios el reparto se queda cerca del 50/50."""
    variants = [
        await get_user_variant(db_session, experiment.id, uuid4())
        for _ in range(100)
    ]

    a_count = variants.count("A")
    b_count = variants.count("B")

    assert a_count + b_count == 100
    assert 30 <= a_count <= 70
    assert 30 <= b_count <= 70


@pytest.mark.asyncio
async def test_assignment_persisted(
    db_session: AsyncSession, experiment: Experiment
) -> None:
    user_id = uuid4()
    variant = await get_user_variant(db_session, experiment.id, user_id)

    assignment = await db_session.scalar(
        select(ExperimentAssignment).where(
            ExperimentAssignment.experiment_id == experiment.id,
            ExperimentAssignment.user_id == user_id,
        )
    )

    assert assignment is not None
    assert assignment.variant == variant


@pytest.mark.asyncio
async def test_only_active_experiments_are_returned(
    db_session: AsyncSession, experiment: Experiment
) -> None:
    """Un experimento en borrador no reparte variantes."""
    draft = Experiment(
        name="test_draft",
        variant_a_label="A",
        variant_b_label="B",
        status="draft",
        started_at=datetime.now(UTC),
    )
    db_session.add(draft)
    await db_session.flush()

    names = {e.name for e in await get_active_experiments(db_session)}
    assert experiment.name in names
    assert "test_draft" not in names
