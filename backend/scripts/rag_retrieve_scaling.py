"""39.32 — scaling comparison for RAGIndex.retrieve() over the REAL content/
corpus, old (dense BM25Okapi.get_scores() + full-corpus candidate scan) vs
new (token-postings index + BM25Okapi.get_batch_scores()).

Loads the real corpus through the production ingestion path
(app.services.content_loader.load_content) into a throwaway in-memory
SQLite DB — same as tests/integration/test_rag_self_retrieval.py — then
times both retrieval strategies at increasing corpus sizes, sampled with a
fixed seed so the run is reproducible.

Usage (from backend/):
    python scripts/rag_retrieve_scaling.py
"""

from __future__ import annotations

import asyncio
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.db import Base
from app.models.content import Question, Skill
from app.services.ai.rag import RAGIndex, _question_documents, _tokenize
from app.services.content_loader import load_content

SEED = 20261002
SIZES = (500, 1500, 3000, 6000)  # plus the full real corpus, appended below
N_QUERIES = 300


async def _load_real_rows():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    async with factory() as db:
        stats = await load_content(db)
        print(f"loaded: {stats}")
        rows = (
            await db.execute(
                select(
                    Question.id, Question.question_es, Question.question_en,
                    Question.explanation_es, Question.explanation_en, Question.source,
                    Question.skill_id,
                )
            )
        ).all()
        skills = {s.id: s for s in (await db.execute(select(Skill))).scalars().all()}
    await engine.dispose()
    return rows, skills


def _old_retrieve(bm25, corpus_tokens, docs, query_tokens, n=3):
    """Pre-39.32 retrieve(): scores the whole corpus every call."""
    query_terms = set(query_tokens)
    scores = bm25.get_scores(query_tokens)
    candidates = [i for i in range(len(docs)) if query_terms.intersection(corpus_tokens[i])]
    candidates.sort(key=lambda i: scores[i], reverse=True)
    return [docs[i].doc_id for i in candidates[:n]]


def _build_queries(rows, skills, sample_n, seed=SEED):
    rng = random.Random(seed)
    sample = rng.sample(rows, min(sample_n, len(rows)))
    return [
        (f"q_{r.id}", f"{(skills.get(r.skill_id).name_es if skills.get(r.skill_id) else '')}: {r.question_es}")
        for r in sample
    ]


def main() -> None:
    rows, skills = asyncio.run(_load_real_rows())
    full_docs = _question_documents(
        [(r.id, r.question_es, r.question_en, r.explanation_es, r.explanation_en, r.source) for r in rows]
    )
    print(f"real corpus questions: {len(full_docs)}")

    sizes = sorted({*(s for s in SIZES if s <= len(full_docs)), len(full_docs)})

    print(f"\n{'N docs':>8}  {'OLD get_scores (s)':>20}  {'NEW batch+invidx (s)':>22}  {'speedup':>8}")
    for n_docs in sizes:
        rng = random.Random(SEED)
        subset_docs = rng.sample(full_docs, n_docs) if n_docs < len(full_docs) else list(full_docs)
        corpus_tokens = [_tokenize(d.text) for d in subset_docs]
        bm25 = BM25Okapi(corpus_tokens)

        idx = RAGIndex()
        idx.index_documents(subset_docs)

        present_ids = {d.doc_id for d in subset_docs}
        queries = [(qid, qtext) for qid, qtext in _build_queries(rows, skills, N_QUERIES) if qid in present_ids]
        if len(queries) < 20:
            queries = [(d.doc_id, d.text[:120]) for d in subset_docs[:N_QUERIES]]

        t0 = time.perf_counter()
        for _qid, qtext in queries:
            _old_retrieve(bm25, corpus_tokens, subset_docs, _tokenize(qtext), n=3)
        t_old = time.perf_counter() - t0

        t0 = time.perf_counter()
        for _qid, qtext in queries:
            idx.retrieve(qtext, n=3)
        t_new = time.perf_counter() - t0

        speedup = t_old / t_new if t_new > 0 else float("inf")
        print(f"{n_docs:>8}  {t_old:>20.3f}  {t_new:>22.3f}  {speedup:>7.1f}x  (n_queries={len(queries)})")


if __name__ == "__main__":
    main()
