"""Glossary endpoints: bilingual (ES/EN) domain terms per track.

Reference content — read-only and unauthenticated (no per-user state)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.content import GlossaryTerm, Track
from app.schemas.content import GlossaryTermRead

router = APIRouter()


@router.get("/{track_id}", response_model=list[GlossaryTermRead])
async def glossary_for_track(
    track_id: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> list[GlossaryTerm]:
    track = await db.get(Track, track_id)
    if track is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found")

    response.headers["Cache-Control"] = "public, max-age=7200, stale-while-revalidate=86400"
    result = await db.execute(
        select(GlossaryTerm)
        .where(GlossaryTerm.track_id == track_id)
        .order_by(GlossaryTerm.order, GlossaryTerm.term_en)
    )
    return list(result.scalars().all())
