"""Unit tests for duplicate_detector.py (5.3).

All tests mock embed_texts so they run without downloading the model.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from app.services.duplicate_detector import (
    DEFAULT_MAX_PAIRS,
    DEFAULT_THRESHOLD,
    DuplicatePair,
    cosine_pairs,
    embed_texts,
    find_duplicates,
)


# ── helpers ────────────────────────────────────────────────────────────────────

def unit_vec(n: int, dim: int = 4) -> np.ndarray:
    """n random unit vectors of dimension dim."""
    rng = np.random.default_rng(0)
    vecs = rng.standard_normal((n, dim)).astype(np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / np.maximum(norms, 1e-9)


def near_duplicate(v: np.ndarray, noise: float = 0.01) -> np.ndarray:
    """Return a unit vector very close to v (similarity ≈ 1 - noise²/2)."""
    rng = np.random.default_rng(1)
    perturbed = v + rng.standard_normal(v.shape).astype(np.float32) * noise
    norm = np.linalg.norm(perturbed)
    return perturbed / max(norm, 1e-9)


# ── embed_texts ────────────────────────────────────────────────────────────────

def test_embed_texts_empty_returns_empty():
    result = embed_texts([])
    assert result.shape == (0, 384)


def test_embed_texts_fallback_when_model_none():
    with patch("app.services.duplicate_detector._load_model", return_value=None):
        result = embed_texts(["hello", "world"])
    assert result.shape == (2, 384)
    norms = np.linalg.norm(result, axis=1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-5)


# ── cosine_pairs ───────────────────────────────────────────────────────────────

def test_cosine_pairs_empty_input():
    pairs = cosine_pairs(np.empty((0, 4), dtype=np.float32), threshold=0.85, max_pairs=100)
    assert pairs == []


def test_cosine_pairs_single_vector():
    vecs = unit_vec(1)
    pairs = cosine_pairs(vecs, threshold=0.85, max_pairs=100)
    assert pairs == []


def test_cosine_pairs_identical_vectors_high_similarity():
    v = unit_vec(1)[0]
    vecs = np.stack([v, v])
    pairs = cosine_pairs(vecs, threshold=0.99, max_pairs=100)
    assert len(pairs) == 1
    i, j, sim = pairs[0]
    assert i == 0 and j == 1
    assert sim > 0.99


def test_cosine_pairs_near_duplicate_detected():
    v = unit_vec(1)[0]
    nd = near_duplicate(v, noise=0.05)
    vecs = np.stack([v, nd])
    pairs = cosine_pairs(vecs, threshold=0.9, max_pairs=100)
    assert len(pairs) == 1
    assert pairs[0][2] > 0.9


def test_cosine_pairs_orthogonal_vectors_not_returned():
    vecs = np.zeros((2, 4), dtype=np.float32)
    vecs[0, 0] = 1.0
    vecs[1, 1] = 1.0  # orthogonal → similarity = 0
    pairs = cosine_pairs(vecs, threshold=0.85, max_pairs=100)
    assert pairs == []


def test_cosine_pairs_no_duplicate_between_self():
    """Each question must not be paired with itself."""
    vecs = unit_vec(5)
    pairs = cosine_pairs(vecs, threshold=0.0, max_pairs=1000)
    for i, j, _ in pairs:
        assert i != j


def test_cosine_pairs_upper_triangle_only():
    """(i, j) and (j, i) should not both appear."""
    vecs = unit_vec(5)
    pairs = cosine_pairs(vecs, threshold=0.0, max_pairs=1000)
    seen: set[tuple[int, int]] = set()
    for i, j, _ in pairs:
        assert i < j, "Lower-triangle pair returned"
        assert (i, j) not in seen
        seen.add((i, j))


def test_cosine_pairs_sorted_by_similarity_descending():
    v = unit_vec(1)[0]
    nd1 = near_duplicate(v, noise=0.01)   # very close
    nd2 = near_duplicate(v, noise=0.30)   # a bit further
    vecs = np.stack([v, nd1, nd2])
    pairs = cosine_pairs(vecs, threshold=0.0, max_pairs=100)
    sims = [p[2] for p in pairs]
    assert sims == sorted(sims, reverse=True)


def test_cosine_pairs_max_pairs_respected():
    vecs = unit_vec(20)
    pairs = cosine_pairs(vecs, threshold=0.0, max_pairs=5)
    assert len(pairs) <= 5


# ── find_duplicates ────────────────────────────────────────────────────────────

@pytest.fixture
def mock_questions() -> list[tuple[str, str]]:
    return [
        ("q001", "What is a Python list?"),
        ("q002", "What is a Python list?"),      # exact duplicate
        ("q003", "Explain the GIL in CPython."),
        ("q004", "What are decorators in Python?"),
    ]


@pytest.mark.asyncio
async def test_find_duplicates_detects_exact_pair(mock_questions: list[tuple[str, str]]) -> None:
    """Identical question texts → returned as a pair."""
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=mock_questions)))

    # Patch embed_texts to return a real model output for controllable similarity
    def fake_embed(texts: list[str], model_name: str = "unused") -> np.ndarray:
        vecs = np.random.default_rng(42).standard_normal((len(texts), 4)).astype(np.float32)
        # Force q001 and q002 to be identical
        if len(texts) >= 2 and texts[0] == texts[1]:
            vecs[1] = vecs[0]
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / np.maximum(norms, 1e-9)

    with patch("app.services.duplicate_detector.embed_texts", side_effect=fake_embed):
        pairs = await find_duplicates(db, threshold=0.99)

    pair_ids = {(p.q1_id, p.q2_id) for p in pairs}
    assert ("q001", "q002") in pair_ids


@pytest.mark.asyncio
async def test_find_duplicates_empty_db() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    pairs = await find_duplicates(db)
    assert pairs == []


@pytest.mark.asyncio
async def test_find_duplicates_single_question() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[("q1", "stem")])))
    pairs = await find_duplicates(db)
    assert pairs == []


@pytest.mark.asyncio
async def test_find_duplicates_returns_duplicate_pair_dataclass(
    mock_questions: list[tuple[str, str]],
) -> None:
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=mock_questions)))

    vecs = np.eye(len(mock_questions), dtype=np.float32)
    vecs[0] = vecs[1]  # q001 = q002

    with patch("app.services.duplicate_detector.embed_texts", return_value=vecs):
        pairs = await find_duplicates(db, threshold=0.99)

    assert all(isinstance(p, DuplicatePair) for p in pairs)
    if pairs:
        p = pairs[0]
        assert 0.0 <= p.similarity <= 1.0
        assert p.q1_stem and p.q2_stem
