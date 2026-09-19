"""Aggregates every v1 endpoint router under a single `api_router`."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    analytics,
    auth,
    billing,
    content,
    duels,
    exams,
    export,
    glossary,
    instructor_marketplace,
    lessons,
    ml,
    oauth,
    placement,
    progress,
    push,
    quiz,
    reports,
    social,
    tutor,
    webhooks,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(oauth.router, prefix="/auth/oauth", tags=["auth"])
api_router.include_router(quiz.router, prefix="/quiz", tags=["quiz"])
api_router.include_router(placement.router, prefix="/placement", tags=["placement"])
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])
api_router.include_router(glossary.router, prefix="/glossary", tags=["glossary"])
api_router.include_router(lessons.router, prefix="/lessons", tags=["lessons"])
api_router.include_router(tutor.router, prefix="/tutor", tags=["tutor"])
api_router.include_router(social.router, tags=["social"])
api_router.include_router(duels.router, prefix="/duels", tags=["duels"])
api_router.include_router(exams.router, prefix="/exams", tags=["exams"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(ml.router, prefix="/ml", tags=["ml"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(push.router, prefix="/push", tags=["push"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(instructor_marketplace.router, prefix="/instructor", tags=["instructor"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
