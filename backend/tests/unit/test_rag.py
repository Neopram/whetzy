"""Unit tests for the RAG service.

Uses a FakeEmbeddingFunction so no model download is required and tests run
in milliseconds. Verifies the full ChromaDB pipeline: index → retrieve.
"""

from __future__ import annotations

import hashlib
import uuid


class FakeEF:
    """Deterministic 384-dim embedding function for tests (no model needed).
    Implements the interface ChromaDB 1.3.2 requires on embedding functions.
    """

    default_space = "cosine"

    def name(self) -> str:
        return "fake-ef"

    def is_legacy(self) -> bool:
        return False

    def _embed(self, texts: list[str]) -> list[list[float]]:
        result = []
        for text in texts:
            h = hashlib.md5(text.encode()).digest()
            raw = [(b / 255.0) - 0.5 for b in h] * 24
            result.append(raw[:384])
        return result

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self._embed(input)

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self._embed(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self._embed(input)


def _make_index(tmp_path) -> "RAGIndex":
    import chromadb
    from app.services.ai.rag import RAGIndex

    client = chromadb.EphemeralClient()
    ef = FakeEF()
    # Use a unique name per test to avoid cross-test contamination
    # (EphemeralClient shares in-process state within a session).
    col = client.get_or_create_collection(
        f"test_{uuid.uuid4().hex}", embedding_function=ef
    )
    # Bypass the PersistentClient constructor; inject the collection directly.
    idx = object.__new__(RAGIndex)
    idx._col = col
    idx._built = False
    return idx


def test_retrieve_returns_relevant_docs(tmp_path):
    idx = _make_index(tmp_path)
    idx._col.upsert(
        ids=["d1", "d2", "d3"],
        documents=[
            "Python list comprehension creates a new list from an iterable",
            "asyncio event loop runs coroutines concurrently",
            "BKT Bayesian Knowledge Tracing models student mastery",
        ],
        metadatas=[{"type": "question"}] * 3,
    )
    idx._built = True

    results = idx.retrieve("list comprehension Python", n=2)

    assert len(results) >= 1
    assert any("list" in r.lower() or "comprehension" in r.lower() for r in results)


def test_retrieve_empty_when_not_built(tmp_path):
    idx = _make_index(tmp_path)
    idx._built = False
    assert idx.retrieve("anything") == []


def test_retrieve_n_capped_to_collection_size(tmp_path):
    idx = _make_index(tmp_path)
    idx._col.upsert(ids=["only"], documents=["solo doc"], metadatas=[{"type": "q"}])
    idx._built = True

    results = idx.retrieve("solo doc", n=10)
    assert len(results) <= 1
