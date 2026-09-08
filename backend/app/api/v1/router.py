"""Aggregates every v1 endpoint router under a single `api_router`."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    duels,
    export,
    glossary,
    placement,
    progress,
    quiz,
    reports,
    social,
    tutor,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(quiz.router, prefix="/quiz", tags=["quiz"])
api_router.include_router(placement.router, prefix="/placement", tags=["placement"])
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])
api_router.include_router(glossary.router, prefix="/glossary", tags=["glossary"])
api_router.include_router(tutor.router, prefix="/tutor", tags=["tutor"])
api_router.include_router(social.router, tags=["social"])
api_router.include_router(duels.router, prefix="/duels", tags=["duels"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
