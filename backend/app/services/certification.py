"""Examen certificador de pago único (38.7, ADR-49).

Un track de certificación tenía simulacro y readiness, pero ningún examen que
emitiera certificado: el simulacro se niega a declarar aprobado contra una escala
oficial que no tenemos. El examen certificador es el mismo sorteo por dominios
con el reloj y el número de preguntas del blueprint oficial, más un umbral que
es **de Whetzy**, dicho en voz alta: `passing_score_pct` del track o el 70 % de
aciertos brutos que usan los finales de track. Aprobarlo emite un «Certificado
Whetzy de preparación», que no sustituye al examen oficial del proveedor.

El acceso cuesta un pago único por track; los reintentos van incluidos. Con
`CERTIFICATION_PAYWALL` apagado (hasta que abra el cobro, H.19) está abierto a
todos, igual que hoy el final de un track de aprendizaje.
"""

from __future__ import annotations

import random
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.content import Track
from app.models.exam import CertificationPurchase, MockExamAttempt
from app.models.user import User
from app.services import mock_exam
from app.services.track_exam import DEFAULT_PASS_PCT, KIND_CERTIFYING

__all__ = ["KIND_CERTIFYING"]
PURCHASE_REQUIRED = "certification_purchase_required"

PASS_NOTE_ES = (
    "El aprobado se fija con el umbral de Whetzy ({pass_pct:g} % de aciertos brutos), "
    "no con la escala oficial del proveedor: el certificado acredita tu preparación "
    "con Whetzy y no sustituye al examen oficial del proveedor."
)
PASS_NOTE_EN = (
    "The pass mark is Whetzy's own ({pass_pct:g} % raw correct), not the vendor's "
    "official scale: the certificate attests your preparation with Whetzy and does "
    "not replace the vendor's official exam."
)


class PaymentRequired(Exception):
    """El paywall está encendido y el usuario no ha comprado este track."""


async def _certification_track(db: AsyncSession, track_id: str) -> Track:
    track = await db.get(Track, track_id)
    if track is None or not track.is_certification:
        raise mock_exam.MockExamError(f"{track_id} is not a certification track")
    return track


async def purchase_for(
    db: AsyncSession, user_id: uuid.UUID, track_id: str
) -> CertificationPurchase | None:
    return (
        await db.scalars(
            select(CertificationPurchase).where(
                CertificationPurchase.user_id == user_id,
                CertificationPurchase.track_id == track_id,
            )
        )
    ).first()


def _staff(user: User) -> bool:
    return bool(user.is_admin or user.role == "owner")


async def access(db: AsyncSession, user: User, track_id: str) -> dict[str, Any]:
    await _certification_track(db, track_id)
    purchased = await purchase_for(db, user.id, track_id) is not None
    return {
        "track_id": track_id,
        "price_usd": settings.CERTIFICATION_PRICE_USD,
        "paywall_enabled": settings.CERTIFICATION_PAYWALL,
        "purchased": purchased,
        "can_start": purchased or _staff(user) or not settings.CERTIFICATION_PAYWALL,
    }


async def grant(
    db: AsyncSession,
    user_id: uuid.UUID,
    track_id: str,
    *,
    source: str,
    price_usd: float | None = None,
    external_ref: str | None = None,
) -> CertificationPurchase:
    """Registra la compra. Idempotente: comprar dos veces no crea dos derechos."""
    await _certification_track(db, track_id)
    existing = await purchase_for(db, user_id, track_id)
    if existing is not None:
        return existing
    purchase = CertificationPurchase(
        id=uuid.uuid4(),
        user_id=user_id,
        track_id=track_id,
        price_usd=settings.CERTIFICATION_PRICE_USD if price_usd is None else price_usd,
        source=source,
        external_ref=external_ref,
    )
    db.add(purchase)
    await db.flush()
    return purchase


async def start(
    db: AsyncSession,
    user: User,
    track_id: str,
    *,
    rng: random.Random | None = None,
) -> MockExamAttempt:
    track = await _certification_track(db, track_id)
    if not (await access(db, user, track_id))["can_start"]:
        raise PaymentRequired(track_id)
    return await mock_exam.start_attempt(
        db,
        user,
        track_id,
        rng=rng,
        kind=KIND_CERTIFYING,
        pass_pct=track.passing_score_pct or DEFAULT_PASS_PCT,
    )


def add_verdict(report: dict[str, Any], attempt: MockExamAttempt) -> dict[str, Any]:
    """Añade el aprobado al informe por dominios del simulacro."""
    pass_pct = attempt.pass_pct if attempt.pass_pct is not None else DEFAULT_PASS_PCT
    return {
        **report,
        "pass_pct": pass_pct,
        "passed": report["raw_pct"] >= pass_pct,
        "pass_note_es": PASS_NOTE_ES.format(pass_pct=pass_pct),
        "pass_note_en": PASS_NOTE_EN.format(pass_pct=pass_pct),
    }
