"""RAG retrieval service — ChromaDB + Sentence Transformers.

Documents indexed (built from the live DB at startup):
  - Question explanations (ES + EN concatenated), tagged with skill_id
  - Glossary term definitions (ES + EN), tagged with track_id

Architecture:
  - PersistentClient: index survives app restarts; auto-resumed when
    collection already has data (skips re-embedding).
  - Background build: `build_bg()` is scheduled as an asyncio.Task during
    lifespan so startup stays instant.
  - Graceful: if chromadb / sentence-transformers are not installed, or the
    build fails, retrieve() returns [] — the tutor falls back to its direct
    explanation without crashing.
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("whetzy.rag")

_COLLECTION_NAME = "whetzy_content"
_EMBED_MODEL = "all-MiniLM-L6-v2"
_BATCH_SIZE = 256

_index: RAGIndex | None = None  # type: ignore[name-defined]  # forward ref resolved below


def _chroma_path() -> str:
    from app.core.config import settings

    p = settings.CHROMA_PERSIST_PATH
    if p:
        return p
    # backend/app/services/ai/rag.py -> parents[3] = backend/
    return str(Path(__file__).resolve().parents[3] / "chroma_db")


class RAGIndex:
    """Thin wrapper around a ChromaDB collection with a lazy-build flag."""

    def __init__(self, persist_path: str, embedding_function=None) -> None:
        import chromadb

        Path(persist_path).mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=persist_path)
        if embedding_function is None:
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

            embedding_function = SentenceTransformerEmbeddingFunction(model_name=_EMBED_MODEL)
        self._col = client.get_or_create_collection(
            name=_COLLECTION_NAME, embedding_function=embedding_function
        )
        count = self._col.count()
        self._built = count > 0
        if self._built:
            logger.info("RAG: resumed existing index (%d docs)", count)

    async def build(self, db: AsyncSession) -> None:
        from app.models.content import GlossaryTerm, Question

        logger.info("RAG: building index from DB…")

        # --- Question explanations -------------------------------------------
        rows = (await db.execute(
            select(
                Question.id,
                Question.explanation_es,
                Question.explanation_en,
                Question.skill_id,
            )
        )).all()

        ids: list[str] = []
        docs: list[str] = []
        metas: list[dict] = []
        for q_id, expl_es, expl_en, skill_id in rows:
            text = " ".join(filter(None, [expl_es, expl_en])).strip()
            if not text:
                continue
            ids.append(f"q_{q_id}")
            docs.append(text)
            metas.append({"type": "question", "skill_id": skill_id or ""})

        for i in range(0, len(ids), _BATCH_SIZE):
            self._col.upsert(
                ids=ids[i : i + _BATCH_SIZE],
                documents=docs[i : i + _BATCH_SIZE],
                metadatas=metas[i : i + _BATCH_SIZE],
            )
        logger.info("RAG: indexed %d question explanations", len(ids))

        # --- Glossary terms --------------------------------------------------
        grows = (await db.execute(
            select(
                GlossaryTerm.id,
                GlossaryTerm.term_es,
                GlossaryTerm.term_en,
                GlossaryTerm.definition_es,
                GlossaryTerm.definition_en,
                GlossaryTerm.track_id,
            )
        )).all()

        g_ids: list[str] = []
        g_docs: list[str] = []
        g_metas: list[dict] = []
        for g_id, t_es, t_en, d_es, d_en, track_id in grows:
            text = f"{t_es} ({t_en}): {d_es}\n{d_en}".strip()
            g_ids.append(f"g_{g_id}")
            g_docs.append(text)
            g_metas.append({"type": "glossary", "track_id": track_id or ""})

        if g_ids:
            self._col.upsert(ids=g_ids, documents=g_docs, metadatas=g_metas)
        logger.info("RAG: indexed %d glossary terms", len(g_ids))

        self._built = True
        logger.info("RAG: index ready (%d docs total)", len(ids) + len(g_ids))

    def retrieve(self, query: str, n: int = 3) -> list[str]:
        if not self._built:
            return []
        try:
            count = self._col.count()
            if count == 0:
                return []
            results = self._col.query(
                query_texts=[query], n_results=min(n, count)
            )
            return [d for d in (results.get("documents") or [[]])[0] if d]
        except Exception:
            logger.exception("RAG retrieve failed")
            return []


async def build_bg(session_factory) -> None:
    """Coroutine to be scheduled with asyncio.create_task() during lifespan."""
    global _index
    try:
        idx = RAGIndex(_chroma_path())
        if not idx._built:
            async with session_factory() as db:
                await idx.build(db)
        _index = idx
    except Exception:
        logger.exception(
            "RAG: background build failed — tutor will use direct explanation only"
        )


def get_index() -> RAGIndex | None:
    return _index


async def retrieve(query: str, n: int = 3) -> list[str]:
    """Return top-n relevant chunks; empty list if index not ready."""
    idx = _index
    if idx is None:
        return []
    return idx.retrieve(query, n)
