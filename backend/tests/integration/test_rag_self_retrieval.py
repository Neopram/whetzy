"""Integration test for the BM25 RAG index (11.1 acceptance criteria):

  - The index is built from the DB (via RAGIndex.build(), the exact method
    app.services.ai.rag.build_bg() calls during lifespan) in well under 2s.
  - Self-retrieval: querying with `"{skill_name}: {question_text}"` — the
    same query shape app.services.ai.tutor.explain_question() builds — finds
    the question's own chunk in the top 3 results for >= 95% of questions,
    in BOTH Spanish and English (bilingual parity, red line #3).
  - Memory: building the index adds well under a per-document budget (see
    _MAX_BYTES_PER_DOC) — bounded per-doc footprint, not a flat ceiling that
    goes stale as the content bank grows.

Loads the *real* content/ JSON corpus (the whole bank, whatever its
current size — see _MIN_CORPUS_QUESTIONS)
through app.services.content_loader.load_content() into a throwaway
in-memory SQLite DB — the same ingestion path used in production — rather
than hitting a prod database, per the task's measurement instructions.
"""

from __future__ import annotations

import time
import tracemalloc

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base
from app.models.content import Question, Skill
from app.services.ai.rag import RAGIndex
from app.services.content_loader import load_content

# Floor, not an exact count: the bank grows. Only catches a truncated tree.
_MIN_CORPUS_QUESTIONS = 1253
_MIN_SELF_RETRIEVAL_PCT = 95.0
_MAX_BUILD_SECONDS = 2.0
# Under a line tracer the build is timing coverage, not the index: the same
# build measures 0.70s clean and 2.01s under `--cov`, and CI runs the whole
# suite with coverage. Asserting 2.0s there makes the test flake on an
# unrelated flag rather than on a real regression, so the strict budget only
# applies untraced; traced runs keep a loose ceiling that still catches a
# pathological blow-up.
_MAX_BUILD_SECONDS_TRACED = 15.0


def _coverage_is_active() -> bool:
    try:
        import coverage
    except ImportError:
        return False
    return coverage.Coverage.current() is not None

# Bytes-per-document, not a fixed ceiling: BM25Okapi's memory is inherently
# ~linear in corpus size (every doc keeps its own token list, plus a
# doc_freqs dict inside rank_bm25), and the content bank grows every
# session — a flat MB ceiling goes stale on legitimate content growth
# instead of catching a real regression.
#
# Measured peak tracemalloc / doc count:
#   1323 docs -> +15.73 MB = 11.89 KB/doc  (task 11.1, docs/AUTONOMOUS_STATE.md)
#   4790 docs -> +57.52 MB = 12.01 KB/doc  (this session, F15-F22 grew the
#                                           bank to 4346 questions / 3 tracks)
# The per-doc footprint drifted ~1% while the corpus grew 3.6x — that's
# linear scaling, not a leak. The budget below keeps 11.1's original ~1.9x
# headroom over the measured per-doc footprint, so it still catches a
# genuine blow-up (e.g. a change that keeps a duplicate copy of the
# tokenized corpus per doc) without going stale as content grows.
_MAX_BYTES_PER_DOC = 24 * 1024  # ~2x headroom over the ~12 KB/doc measured


async def _load_real_corpus() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    async with factory() as db:
        stats = await load_content(db)
    # The guard here is "the corpus loaded COMPLETELY", not "the corpus is
    # exactly N questions" — the bank grows every content session, and pinning
    # an exact count makes an unrelated content commit fail this test (it did:
    # 11.4 added 104 exec questions). `skipped == 0` is the assertion that
    # actually protects the percentage below; the floor just catches a corpus
    # that failed to load at all.
    assert stats["skipped"] == 0, (
        f"{stats['skipped']} questions were skipped on load — self-retrieval % "
        "below would be measured against a partial corpus."
    )
    assert stats["questions"] >= _MIN_CORPUS_QUESTIONS, (
        f"Only {stats['questions']} questions loaded (expected at least "
        f"{_MIN_CORPUS_QUESTIONS}) — the content tree looks truncated."
    )
    return factory


async def test_index_builds_fast_with_bounded_memory_and_hits_self_retrieval_bar() -> None:
    factory = await _load_real_corpus()

    async with factory() as db:
        idx = RAGIndex()

        tracemalloc.start()
        t0 = time.perf_counter()
        await idx.build(db)
        build_seconds = time.perf_counter() - t0
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"\nRAG index build: {build_seconds:.3f}s, {len(idx._docs)} docs, peak +{peak / 1e6:.2f} MB")
        traced = _coverage_is_active()
        budget = _MAX_BUILD_SECONDS_TRACED if traced else _MAX_BUILD_SECONDS
        assert build_seconds < budget, (
            f"Index build took {build_seconds:.3f}s, over the {budget}s budget"
            + (" (measured under a coverage tracer)" if traced else "")
        )
        budget_bytes = len(idx._docs) * _MAX_BYTES_PER_DOC
        assert peak < budget_bytes, (
            f"Index build allocated {peak / 1e6:.2f} MB for {len(idx._docs)} docs "
            f"({peak / len(idx._docs):.0f} B/doc), over the {_MAX_BYTES_PER_DOC / 1024:.0f} "
            f"KB/doc budget ({budget_bytes / 1e6:.2f} MB total)"
        )

        rows = (
            await db.execute(
                select(Question.id, Question.question_es, Question.question_en, Question.skill_id)
            )
        ).all()
        skills = {s.id: s for s in (await db.execute(select(Skill))).scalars().all()}

        for lang in ("es", "en"):
            hits = 0
            hits_with_source = 0
            misses: list[str] = []
            for q_id, q_es, q_en, skill_id in rows:
                skill = skills.get(skill_id)
                skill_name = (skill.name_es if lang == "es" else skill.name_en) if skill else ""
                q_text = q_es if lang == "es" else q_en
                query = f"{skill_name}: {q_text}"

                top3 = idx.retrieve(query, n=3)
                top3_ids = [chunk.doc_id for chunk in top3]
                if f"q_{q_id}" in top3_ids:
                    hits += 1
                    self_chunk = next(c for c in top3 if c.doc_id == f"q_{q_id}")
                    if self_chunk.source:
                        hits_with_source += 1
                else:
                    misses.append(q_id)

            pct = 100 * hits / len(rows)
            print(
                f"[{lang}] self-retrieval top-3: {hits}/{len(rows)} = {pct:.2f}% "
                f"(with source: {hits_with_source}/{hits}); sample misses: {misses[:5]}"
            )
            assert pct >= _MIN_SELF_RETRIEVAL_PCT, (
                f"[{lang}] self-retrieval only {pct:.2f}% (< {_MIN_SELF_RETRIEVAL_PCT}%). "
                f"Misses (first 10): {misses[:10]}"
            )
            # Every question in content/ carries a `source` citation, so a
            # self-hit should carry one too — this is the exact fact tutor.py
            # uses to decide `grounded`.
            assert hits_with_source == hits


async def test_retrieve_returns_nothing_for_a_query_with_no_shared_vocabulary() -> None:
    """Honesty check at integration scale: even against the full corpus, an
    unrelated query must not be padded with unrelated "grounding"."""
    factory = await _load_real_corpus()
    async with factory() as db:
        idx = RAGIndex()
        await idx.build(db)

    # Real English/Spanish words (even ones that sound like filler, e.g.
    # "token") show up somewhere in 1323 technical documents — this query
    # must be pure gibberish to genuinely share zero tokens with the corpus.
    results = idx.retrieve("zzxqqjjhh wwvvbbnnmm qqppoolliikk xxzzyyqqww", n=3)
    assert results == []
