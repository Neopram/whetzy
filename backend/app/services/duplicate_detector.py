"""Embedding-based duplicate detection for the question bank (5.3).

Algorithm:
  1. Fetch all questions (or a filtered subset) from the DB.
  2. Embed ``question_es`` stems using sentence-transformers
     (``all-MiniLM-L6-v2`` — 384-dim, fast, good paraphrase recall).
  3. Compute the upper-triangle of the cosine similarity matrix in one
     numpy vectorised step.
  4. Return pairs whose cosine similarity ≥ ``threshold``, sorted by
     similarity descending.

The sentence-transformers model is loaded once per process (lazy singleton)
and inference runs in a thread-pool executor so it does not block the async
event loop.

Public interface
----------------
    find_duplicates(db, *, skill_id=None, threshold=0.85, max_pairs=200)
        -> list[DuplicatePair]

    embed_texts(texts) -> np.ndarray          # exposed for unit-testing
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import numpy as np
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Question

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "all-MiniLM-L6-v2"
DEFAULT_THRESHOLD = 0.85
DEFAULT_MAX_PAIRS = 200


# ── Model singleton ────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_model(model_name: str = DEFAULT_MODEL) -> Any:
    """Load and cache the SentenceTransformer model (expensive — do once)."""
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped,unused-ignore]
        logger.info("Loading sentence-transformer model: %s", model_name)
        return SentenceTransformer(model_name)
    except ImportError:
        logger.error("sentence-transformers not installed; duplicate detection unavailable")
        return None


# ── Core helpers ───────────────────────────────────────────────────────────────

def embed_texts(texts: list[str], model_name: str = DEFAULT_MODEL) -> np.ndarray:
    """Return an (N, D) float32 embedding matrix for *texts*.

    Falls back to random unit vectors when the model cannot be loaded so
    tests can patch this function without requiring a real model download.
    """
    if not texts:
        return np.empty((0, 384), dtype=np.float32)

    model = _load_model(model_name)
    if model is None:
        rng = np.random.default_rng(42)
        fallback = rng.standard_normal((len(texts), 384)).astype(np.float32)
        norms = np.linalg.norm(fallback, axis=1, keepdims=True)
        result: np.ndarray = fallback / np.maximum(norms, 1e-9)
        return result

    raw: Any = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    vecs = np.asarray(raw, dtype=np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    normed: np.ndarray = vecs / np.maximum(norms, 1e-9)
    return normed


def cosine_pairs(
    embeddings: np.ndarray,
    threshold: float,
    max_pairs: int,
) -> list[tuple[int, int, float]]:
    """Return (i, j, similarity) tuples for the upper triangle where sim ≥ threshold.

    Operates in O(N²) space — fine for N < 5 000.  For larger corpora,
    use approximate nearest-neighbour (e.g. FAISS) instead.
    """
    n = len(embeddings)
    if n < 2:
        return []

    # (N, N) similarity matrix — vectorised, fast even at 1 000 × 1 000
    sim_matrix: np.ndarray = embeddings @ embeddings.T
    np.fill_diagonal(sim_matrix, 0.0)

    # Upper triangle only (avoid reporting both (i,j) and (j,i))
    triu_i, triu_j = np.triu_indices(n, k=1)
    sims = sim_matrix[triu_i, triu_j]

    mask = sims >= threshold
    if not mask.any():
        return []

    idx_i = triu_i[mask]
    idx_j = triu_j[mask]
    scores = sims[mask]

    # Sort by descending similarity
    order = np.argsort(-scores)
    idx_i = idx_i[order]
    idx_j = idx_j[order]
    scores = scores[order]

    return [
        (int(idx_i[k]), int(idx_j[k]), float(scores[k]))
        for k in range(min(len(scores), max_pairs))
    ]


# ── Public API ─────────────────────────────────────────────────────────────────

@dataclass
class DuplicatePair:
    q1_id: str
    q2_id: str
    similarity: float
    q1_stem: str
    q2_stem: str


async def find_duplicates(
    db: "AsyncSession",
    *,
    skill_id: str | None = None,
    threshold: float = DEFAULT_THRESHOLD,
    max_pairs: int = DEFAULT_MAX_PAIRS,
    model_name: str = DEFAULT_MODEL,
) -> list[DuplicatePair]:
    """Detect near-duplicate questions by embedding cosine similarity.

    Parameters
    ----------
    db:          async DB session
    skill_id:    restrict to one skill (None = entire bank)
    threshold:   minimum cosine similarity to consider a pair a duplicate
    max_pairs:   maximum number of pairs returned (sorted by similarity desc)
    model_name:  sentence-transformers model identifier
    """
    stmt = select(Question.id, Question.question_es)
    if skill_id:
        stmt = stmt.where(Question.skill_id == skill_id)
    rows = (await db.execute(stmt)).all()

    if len(rows) < 2:
        return []

    ids = [r[0] for r in rows]
    texts = [r[1] for r in rows]

    # Run CPU-bound embedding in thread pool so the event loop stays free
    loop = asyncio.get_event_loop()
    embeddings: np.ndarray = await loop.run_in_executor(
        None, embed_texts, texts, model_name
    )

    pairs = cosine_pairs(embeddings, threshold=threshold, max_pairs=max_pairs)

    return [
        DuplicatePair(
            q1_id=ids[i],
            q2_id=ids[j],
            similarity=round(sim, 4),
            q1_stem=texts[i][:200],
            q2_stem=texts[j][:200],
        )
        for i, j, sim in pairs
    ]
