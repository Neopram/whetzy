"""RAG retrieval service — pure-Python BM25 (rank-bm25), no torch/ChromaDB.

Documents indexed (built from the live DB at startup):
  - Question chunks: explanation (ES + EN) folded together with the
    question's own wording (ES + EN), tagged with the question's `source`
    citation. Folding the question text in (not just the explanation) is
    what makes self-retrieval work in practice — see the module docstring
    of tests/unit/test_rag.py for the measured numbers.
  - Glossary term chunks: term + definition (ES + EN), tagged with the
    term's `source` citation.

Architecture:
  - In-memory only: `rank_bm25.BM25Okapi` over a tokenized corpus. No
    persistence, no native extensions, no model download — building the
    full ~1250-question + glossary corpus takes well under a second, so
    there is no need for ChromaDB's on-disk persistence/resume dance.
  - Background build: `build_bg()` is scheduled as an asyncio.Task during
    lifespan so startup stays instant; the index itself finishes building
    in a fraction of a second once that task runs.
  - Honest grounding: `retrieve()` only returns chunks that actually share a
    token with the query — it never pads results with unrelated documents
    just to fill up to n (see `RAGIndex.retrieve` docstring for why this is
    a token-overlap check rather than a BM25-score-sign check). Callers can
    check `RetrievedChunk.source` to know whether a hit carries a real
    citation; there is no notion of "grounded" inside this module itself,
    that judgment belongs to the caller (see app.services.ai.tutor).
  - Graceful: if the index hasn't been built yet (still starting up, or a
    background build failed), retrieve() returns [] — the tutor falls back
    to its direct explanation without crashing.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("whetzy.rag")

_TOKEN_RE = re.compile(r"[a-zA-ZÀ-ÿ0-9_]+")


def _tokenize(text: str) -> list[str]:
    """Lowercase word tokenizer for BM25 over bilingual (ES/EN) technical prose.

    Keeps alphanumerics and underscores (so `list_comprehension`, `__init__`
    tokenize as single terms). No stemming/accent-folding is applied — BM25
    matches on exact tokens, and ES/EN share enough ASCII vocabulary
    (identifiers, keywords, borrowed technical terms, and — critically — the
    question's own wording folded into each document, see module docstring)
    for solid cross-language recall without one.
    """
    return _TOKEN_RE.findall(text.lower())


@dataclass(frozen=True)
class RetrievedChunk:
    """One retrieved grounding fragment."""

    doc_id: str
    text: str
    source: str | None
    kind: str  # "question" | "glossary"


def _question_documents(rows: Iterable[Any]) -> list[RetrievedChunk]:
    """Build one chunk per question from `(id, question_es, question_en,
    explanation_es, explanation_en, source)` rows — either plain tuples
    (tests) or SQLAlchemy `Row` objects (`build()`), both unpack the same
    way."""
    docs: list[RetrievedChunk] = []
    for q_id, q_es, q_en, expl_es, expl_en, source in rows:
        text = " ".join(filter(None, [expl_es, expl_en, q_es, q_en])).strip()
        if not text:
            continue
        docs.append(RetrievedChunk(doc_id=f"q_{q_id}", text=text, source=source, kind="question"))
    return docs


def _glossary_documents(rows: Iterable[Any]) -> list[RetrievedChunk]:
    """Build one chunk per glossary term from `(id, term_es, term_en,
    definition_es, definition_en, source)` rows — either plain tuples
    (tests) or SQLAlchemy `Row` objects (`build()`), both unpack the same
    way."""
    docs: list[RetrievedChunk] = []
    for g_id, t_es, t_en, d_es, d_en, source in rows:
        text = f"{t_es} ({t_en}): {d_es}\n{d_en}".strip()
        docs.append(RetrievedChunk(doc_id=f"g_{g_id}", text=text, source=source, kind="glossary"))
    return docs


class RAGIndex:
    """A BM25 index over question + glossary chunks, built once from the DB."""

    def __init__(self) -> None:
        self._docs: list[RetrievedChunk] = []
        self._corpus_tokens: list[list[str]] = []
        self._bm25: BM25Okapi | None = None
        self._built = False

    def index_documents(self, docs: Sequence[RetrievedChunk]) -> None:
        """DB-free indexing step: tokenize + build the BM25 index.

        Split out from `build()` so it can be exercised directly by tests
        (and any future non-DB corpus, e.g. loading straight from the
        content/ JSON files) without needing a database session.
        """
        self._docs = list(docs)
        self._corpus_tokens = [_tokenize(d.text) for d in self._docs]
        self._bm25 = BM25Okapi(self._corpus_tokens) if self._corpus_tokens else None
        self._built = True

    async def build(self, db: AsyncSession) -> None:
        from app.models.content import GlossaryTerm, Question

        logger.info("RAG: building BM25 index from DB…")

        q_rows = (
            await db.execute(
                select(
                    Question.id,
                    Question.question_es,
                    Question.question_en,
                    Question.explanation_es,
                    Question.explanation_en,
                    Question.source,
                )
            )
        ).all()
        docs = _question_documents(q_rows)

        g_rows = (
            await db.execute(
                select(
                    GlossaryTerm.id,
                    GlossaryTerm.term_es,
                    GlossaryTerm.term_en,
                    GlossaryTerm.definition_es,
                    GlossaryTerm.definition_en,
                    GlossaryTerm.source,
                )
            )
        ).all()
        docs.extend(_glossary_documents(g_rows))

        self.index_documents(docs)
        logger.info(
            "RAG: index ready (%d docs: %d questions, %d glossary terms)",
            len(docs),
            len(q_rows),
            len(g_rows),
        )

    def retrieve(self, query: str, n: int = 3) -> list[RetrievedChunk]:
        """Return up to n chunks that share at least one term with *query*,
        ranked by BM25 score.

        Never pads with unrelated documents: a chunk is only kept if it
        actually shares a token with the query, so an empty result honestly
        means "nothing in the index matches this query" rather than "here
        are the n least-irrelevant documents". Token overlap — not the raw
        BM25 score sign — is what decides inclusion: BM25Okapi's
        negative-IDF epsilon-smoothing (see rank_bm25's `_calc_idf`) can make
        a genuinely-overlapping document score at or below zero in a small
        or highly homogeneous corpus, which a score-sign filter would wrongly
        drop.
        """
        if not self._built or self._bm25 is None or not self._docs:
            return []
        tokens = _tokenize(query)
        if not tokens:
            return []
        query_terms = set(tokens)
        try:
            scores = self._bm25.get_scores(tokens)
        except Exception:
            logger.exception("RAG retrieve failed")
            return []
        # Filter to actually-overlapping docs *before* ranking: a
        # non-overlapping doc always scores exactly 0, but epsilon-smoothing
        # (see docstring above) can push a genuinely-overlapping doc's score
        # slightly *below* 0 in small/homogeneous corpora — ranking first
        # would then bury it under non-matches instead of surfacing it.
        candidates = [i for i in range(len(self._docs)) if query_terms.intersection(self._corpus_tokens[i])]
        candidates.sort(key=lambda i: scores[i], reverse=True)
        return [self._docs[i] for i in candidates[:n]]


_index: RAGIndex | None = None


async def build_bg(session_factory: Any) -> None:
    """Coroutine to be scheduled with asyncio.create_task() during lifespan."""
    global _index
    try:
        idx = RAGIndex()
        async with session_factory() as db:
            await idx.build(db)
        _index = idx
    except Exception:
        logger.exception(
            "RAG: background build failed — tutor will use direct explanation only"
        )


def get_index() -> RAGIndex | None:
    return _index


async def retrieve(query: str, n: int = 3) -> list[RetrievedChunk]:
    """Return up to n relevant chunks; empty list if the index isn't ready."""
    idx = _index
    if idx is None:
        return []
    return idx.retrieve(query, n)
