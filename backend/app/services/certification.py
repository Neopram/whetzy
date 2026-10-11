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
from sqlalchemy.exc import IntegrityError
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


NOT_AVAILABLE = "certification_not_available"


class NotAvailable(Exception):
    """Todavía no hay banco reservado: el examen saldría del banco de práctica."""


def _certification_available() -> bool:
    """Con el banco reservado apagado el examen sortea del mismo banco que la
    práctica, así que el certificado mediría en parte preguntas memorizadas
    (auditoría 2026-10-11, N6). Se abre cuando se abre el banco reservado."""
    return settings.MOCK_EXAM_RESERVED_POOL_ENABLED


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
    available = _certification_available()
    paid_or_free = purchased or not settings.CERTIFICATION_PAYWALL
    return {
        "track_id": track_id,
        "price_usd": settings.CERTIFICATION_PRICE_USD,
        "paywall_enabled": settings.CERTIFICATION_PAYWALL,
        "purchased": purchased,
        "available": available,
        "can_start": _staff(user) or (available and paid_or_free),
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
    """Registra la compra. Idempotente: comprar dos veces no crea dos derechos.

    Un reintento de Paddle del mismo webhook de compra puede llegar mientras
    el primero todavía no ha hecho commit — el `SELECT` de arriba no lo ve
    todavía, así que el `INSERT` necesita su propia red de seguridad contra
    la unique constraint (user_id, track_id), no solo el check previo.
    """
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
    try:
        async with db.begin_nested():
            db.add(purchase)
            await db.flush()
    except IntegrityError:
        existing = await purchase_for(db, user_id, track_id)
        if existing is not None:
            return existing
        raise
    return purchase


async def revoke_purchase_by_external_ref(db: AsyncSession, external_ref: str) -> bool:
    """Retira el derecho de examen que ese cargo de Paddle concedió (reembolso).

    Por `external_ref` (el id de la transacción), no por (user_id, track_id):
    así un reembolso solo toca la compra que de verdad pagó esa transacción,
    nunca una compra posterior y distinta del mismo usuario/track. Sin fila
    de "revocado" en `certification_purchases` (sería otra migración; la 54
    ya está en curso, una a la vez) se borra: sin ella, `purchase_for` ya
    vuelve a dar None, que es justo lo que pasaba antes de pagar.
    Idempotente: si no hay ninguna compra con ese external_ref (ya revocada,
    o un reembolso repetido), no hace nada y devuelve False.
    """
    existing = (
        await db.scalars(
            select(CertificationPurchase).where(
                CertificationPurchase.external_ref == external_ref
            )
        )
    ).first()
    if existing is None:
        return False
    await db.delete(existing)
    await db.flush()
    return True


async def start(
    db: AsyncSession,
    user: User,
    track_id: str,
    *,
    rng: random.Random | None = None,
) -> MockExamAttempt:
    track = await _certification_track(db, track_id)
    state = await access(db, user, track_id)
    if not state["can_start"]:
        if not state["available"]:
            raise NotAvailable(track_id)
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
