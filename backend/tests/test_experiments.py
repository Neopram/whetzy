"""Test A/B experiment framework."""

import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models.experiment import Experiment, ExperimentAssignment
from app.services.experiments import get_user_variant, get_active_experiments
from datetime import datetime


@pytest.fixture
def experiment(db: Session):
    """Create a test experiment."""
    exp = Experiment(
        name="test_cta_landing",
        description="CTA button color test",
        variant_a_label="Blue",
        variant_b_label="Green",
        hypothesis="Green CTA increases signups by 5%",
        status="active",
        started_at=datetime.now()
    )
    db.add(exp)
    db.commit()
    return exp


def test_deterministic_variant_assignment(db: Session, experiment: Experiment):
    """Same user should always get same variant."""
    user_id = uuid4()
    
    variant1 = get_user_variant(db, experiment.id, user_id)
    variant2 = get_user_variant(db, experiment.id, user_id)
    
    assert variant1 == variant2
    assert variant1 in ("A", "B")


def test_variant_distribution(db: Session, experiment: Experiment):
    """Test that variants distribute roughly 50/50 across many users."""
    num_users = 100
    users = [uuid4() for _ in range(num_users)]
    
    variants = [get_user_variant(db, experiment.id, uid) for uid in users]
    
    a_count = sum(1 for v in variants if v == "A")
    b_count = sum(1 for v in variants if v == "B")
    
    assert a_count + b_count == num_users
    assert 30 <= a_count <= 70  # Roughly 50/50
    assert 30 <= b_count <= 70


def test_assignment_persisted(db: Session, experiment: Experiment):
    """Assignment should be saved to database."""
    user_id = uuid4()
    
    variant = get_user_variant(db, experiment.id, user_id)
    
    assignment = db.query(ExperimentAssignment).filter(
        ExperimentAssignment.experiment_id == experiment.id,
        ExperimentAssignment.user_id == user_id
    ).first()
    
    assert assignment is not None
    assert assignment.variant == variant
