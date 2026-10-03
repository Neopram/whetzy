"""Unit tests for the BM25 RAG service (11.1).

No chromadb, no sentence-transformers, no model download: `rank-bm25` is
pure Python over a plain word tokenizer, so these tests run in milliseconds
and need nothing beyond what's in requirements.txt.

Self-retrieval measurement (full 1253-question content/ corpus, real DB
round-trip via app.services.content_loader) lives in
tests/integration/test_rag_self_retrieval.py — this file covers the unit
building blocks: tokenizer, document builders, and RAGIndex.retrieve().
"""

from __future__ import annotations

from app.services.ai.rag import (
    RAGIndex,
    RetrievedChunk,
    _glossary_documents,
    _question_documents,
    _tokenize,
)

# ── Tokenizer ──────────────────────────────────────────────────────────────


def test_tokenize_lowercases_and_splits_on_punctuation() -> None:
    assert _tokenize("List Comprehension: Creates a NEW list!") == [
        "list",
        "comprehension",
        "creates",
        "a",
        "new",
        "list",
    ]


def test_tokenize_keeps_identifiers_with_underscores_intact() -> None:
    assert _tokenize("__init__ and list_comprehension") == [
        "__init__",
        "and",
        "list_comprehension",
    ]


def test_tokenize_empty_string_is_empty_list() -> None:
    assert _tokenize("") == []
    assert _tokenize("   ") == []


# ── Document builders (pure, DB-free) ───────────────────────────────────────


def test_question_documents_folds_question_and_explanation_together() -> None:
    rows = [
        (
            "q1",
            "¿Qué es una lista?",
            "What is a list?",
            "Una lista es mutable.",
            "A list is mutable.",
            "CPython docs 3.13",
        )
    ]
    docs = _question_documents(rows)

    assert len(docs) == 1
    doc = docs[0]
    assert doc.doc_id == "q_q1"
    assert doc.kind == "question"
    assert doc.source == "CPython docs 3.13"
    # Both languages, question wording AND explanation wording, all present —
    # this is what makes self-retrieval work (see test_rag_self_retrieval.py).
    for expected in ["lista", "list", "mutable", "Una lista es mutable"]:
        assert expected.lower() in doc.text.lower()


def test_question_documents_skips_rows_with_no_text_anywhere() -> None:
    rows = [("q_empty", "", "", "", "", None)]
    assert _question_documents(rows) == []


def test_question_documents_handles_missing_source() -> None:
    rows = [("q1", "pregunta", "question", "explicación", "explanation", None)]
    docs = _question_documents(rows)
    assert docs[0].source is None


def test_glossary_documents_builds_bilingual_chunk() -> None:
    rows = [("g1", "Variable", "Variable", "Un nombre enlazado.", "A bound name.", "PEP 8")]
    docs = _glossary_documents(rows)

    assert len(docs) == 1
    doc = docs[0]
    assert doc.doc_id == "g_g1"
    assert doc.kind == "glossary"
    assert doc.source == "PEP 8"
    assert "Variable" in doc.text
    assert "Un nombre enlazado" in doc.text
    assert "A bound name" in doc.text


# ── RAGIndex.retrieve() ──────────────────────────────────────────────────────


def _index_from(docs: list[RetrievedChunk]) -> RAGIndex:
    idx = RAGIndex()
    idx.index_documents(docs)
    return idx


def test_retrieve_returns_relevant_docs() -> None:
    idx = _index_from(
        [
            RetrievedChunk(
                doc_id="d1",
                text="Python list comprehension creates a new list from an iterable",
                source="CPython docs",
                kind="question",
            ),
            RetrievedChunk(
                doc_id="d2",
                text="asyncio event loop runs coroutines concurrently",
                source="asyncio docs",
                kind="question",
            ),
            RetrievedChunk(
                doc_id="d3",
                text="BKT Bayesian Knowledge Tracing models student mastery",
                source=None,
                kind="question",
            ),
        ]
    )

    results = idx.retrieve("list comprehension Python", n=2)

    assert 1 <= len(results) <= 2
    assert any("list" in r.text.lower() or "comprehension" in r.text.lower() for r in results)


def test_retrieve_empty_before_index_documents_called() -> None:
    idx = RAGIndex()
    assert idx.retrieve("anything") == []


def test_retrieve_empty_query_returns_empty() -> None:
    idx = _index_from(
        [RetrievedChunk(doc_id="d1", text="solo doc", source=None, kind="question")]
    )
    assert idx.retrieve("   ") == []


def test_retrieve_n_capped_to_collection_size() -> None:
    idx = _index_from(
        [RetrievedChunk(doc_id="only", text="solo doc", source=None, kind="question")]
    )
    results = idx.retrieve("solo doc", n=10)
    assert len(results) <= 1


def test_retrieve_never_pads_with_unrelated_documents() -> None:
    """A query sharing no term with anything in the index must return []
    rather than the "least bad" n documents — grounded must never be faked."""
    idx = _index_from(
        [
            RetrievedChunk(doc_id="d1", text="asyncio coroutines", source="x", kind="question"),
            RetrievedChunk(doc_id="d2", text="list comprehension", source="y", kind="question"),
        ]
    )
    assert idx.retrieve("xyzzy plugh completely unrelated gibberish qqqzzz", n=3) == []


def test_retrieve_carries_source_through_for_grounding() -> None:
    idx = _index_from(
        [RetrievedChunk(doc_id="q_1", text="mutable default arguments", source="PEP 8", kind="question")]
    )
    results = idx.retrieve("mutable default arguments")
    assert len(results) == 1
    assert results[0].source == "PEP 8"


def test_retrieve_unions_candidates_across_all_query_terms() -> None:
    """Every query term must contribute candidates, not just one of them —
    a document that shares only a *different* query term than its sibling
    must still surface (39.32: retrieve() finds candidates via a per-term
    postings lookup in `_token_to_docs`; dropping any query term from that
    union would silently lose whichever documents only matched on it, and
    no other test here would notice)."""
    idx = _index_from(
        [
            RetrievedChunk(doc_id="d1", text="alpha only here", source=None, kind="question"),
            RetrievedChunk(doc_id="d2", text="gamma only here", source=None, kind="question"),
        ]
    )
    results = idx.retrieve("alpha gamma", n=2)
    assert {r.doc_id for r in results} == {"d1", "d2"}


def test_retrieve_bilingual_query_matches_either_language() -> None:
    """Red line: the index must cover ES and EN — a document built from both
    languages should be retrievable by a query in just one of them."""
    idx = _index_from(_question_documents([("q1", "¿Qué es un decorador?", "What is a decorator?", "Envuelve una función.", "It wraps a function.", "PEP 318")]))

    es_hit = idx.retrieve("decorador")
    en_hit = idx.retrieve("decorator")

    assert len(es_hit) == 1 and es_hit[0].doc_id == "q_q1"
    assert len(en_hit) == 1 and en_hit[0].doc_id == "q_q1"
