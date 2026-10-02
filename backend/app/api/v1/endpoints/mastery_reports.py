"""Informe de dominio (ECONOMIA §2.3): comprarlo con créditos, listarlos y la
página pública por código."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.economy import MasteryReport
from app.models.user import User
from app.services import mastery_report as service

router = APIRouter()


class BuyRequest(BaseModel):
    # Lo genera el cliente por intento de compra: reintentar no cobra dos veces.
    request_id: uuid.UUID


def _public(report: MasteryReport) -> dict[str, Any]:
    return {"code": report.code, "created_at": report.created_at.isoformat(), "snapshot": report.snapshot}


@router.post("", status_code=status.HTTP_201_CREATED)
async def buy_mastery_report(
    body: BuyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Cobra 300 créditos y publica el informe; 409 `insufficient_credits`."""
    try:
        report = await service.buy(db, current_user, str(body.request_id))
    except service.InsufficientCredits as exc:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "insufficient_credits") from exc
    await db.commit()
    return _public(report)


@router.get("")
async def my_mastery_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = (
        await db.execute(
            select(MasteryReport)
            .where(MasteryReport.user_id == current_user.id)
            .order_by(desc(MasteryReport.created_at))
        )
    ).scalars().all()
    return {"reports": [{"code": r.code, "created_at": r.created_at.isoformat()} for r in rows]}


@router.get("/{code}")
async def get_mastery_report(code: str, response: Response, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Pública, **sin autenticación a propósito**, como un certificado: quien
    tiene que leerla (un empleador) no tiene cuenta. La única llave es un código
    de 128 bits que solo llega a alguien porque el titular se lo dio."""
    report = (await db.execute(select(MasteryReport).where(MasteryReport.code == code))).scalar_one_or_none()
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "report not found")
    response.headers["Cache-Control"] = "public, max-age=3600"
    return _public(report)
