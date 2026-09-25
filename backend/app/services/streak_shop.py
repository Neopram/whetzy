"""Tienda de la racha: comprar comodines con créditos (ledger 35.3).

La racha amable tiene dos fuentes de comodines:

* **Gratis:** uno por semana ISO si no te queda ninguno (`quiz._update_streak`).
* **Comprados:** este módulo. 150 créditos cada uno, el precio que ya publicaba
  `GET /economy/prices` sin que hubiera forma de pagarlo.

Tres reglas para que la tienda no convierta la racha en algo que se compra:

1. **Tope de comodines guardados** (`MAX_FREEZES_HELD`). Un comodín cubre un día
   suelto; guardar veinte sería comprar semanas enteras sin estudiar.
2. **Tope de compras por semana ISO** (`MAX_PURCHASES_PER_WEEK`). Aunque tengas
   créditos, una racha sostenida a base de compras deja de medir constancia.
3. **Nunca con dinero, solo con créditos** (ECONOMIA.md: los créditos se ganan
   estudiando). Mimo cobra la reparación de racha en su plan de pago;
   COMPETENCIA.md §A.4 lo descarta a propósito.

Y dos de corrección, porque el cargo es dinero de juego pero de verdad:

* **Idempotente por `request_id`.** El cliente genera un UUID por intento; un
  doble toque o un reintento de red con el mismo id devuelve el resultado de la
  primera compra y no cobra dos veces. El id viaja como `ref_id` del cargo en el
  ledger, que es inmutable, así que la prueba de «ya se cobró» es el propio
  cargo, no un estado aparte que se pueda desincronizar.
* **Serializado por usuario.** La fila del usuario se bloquea (`FOR UPDATE`)
  antes de leer saldo, topes y comodines: dos compras simultáneas con ids
  distintos no pueden pasar las dos el tope ni gastar el mismo saldo. En SQLite
  (tests) el bloqueo no existe y no hace falta: hay una sola conexión.

La semana de compra se guarda en `ref_type` (`streak_freeze:2026-W39`) y no se
calcula con `created_at`: así el recuento es una igualdad de texto, igual en
Postgres y en SQLite, sin depender de cómo guarda cada uno la zona horaria.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.economy import CreditLedger, CreditReasonEnum
from app.models.user import User
from app.services.economy import CreditsService

FREEZE_PRICE_CREDITS = 150
MAX_FREEZES_HELD = 3
MAX_PURCHASES_PER_WEEK = 2

BlockReason = Literal["insufficient_credits", "max_held", "weekly_limit"]


class FreezePurchaseError(Exception):
    """La compra no procede; `reason` es estable y el cliente la traduce."""

    def __init__(self, reason: BlockReason) -> None:
        super().__init__(reason)
        self.reason: BlockReason = reason


@dataclass(frozen=True)
class FreezeQuote:
    price: int
    balance: int
    held: int
    max_held: int
    purchases_this_week: int
    max_per_week: int
    can_buy: bool
    blocked_by: BlockReason | None


def iso_week_key(now: datetime) -> str:
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"


def _ref_type(now: datetime) -> str:
    return f"streak_freeze:{iso_week_key(now)}"


async def _purchases_this_week(db: AsyncSession, user_id: uuid.UUID, now: datetime) -> int:
    # Una compra puede consumir varios lotes (varias filas con el mismo ref_id):
    # se cuentan ids distintos, no filas.
    result = await db.execute(
        select(func.count(func.distinct(CreditLedger.ref_id))).where(
            CreditLedger.user_id == user_id,
            CreditLedger.reason == CreditReasonEnum.SPEND_FREEZE.value,
            CreditLedger.ref_type == _ref_type(now),
        )
    )
    return int(result.scalar() or 0)


async def quote(db: AsyncSession, user: User, now: datetime | None = None) -> FreezeQuote:
    now = now or datetime.now(UTC)
    balance = await CreditsService.get_balance(db, user.id)
    bought = await _purchases_this_week(db, user.id, now)
    held = user.streak_freeze_available

    blocked_by: BlockReason | None = None
    if held >= MAX_FREEZES_HELD:
        blocked_by = "max_held"
    elif bought >= MAX_PURCHASES_PER_WEEK:
        blocked_by = "weekly_limit"
    elif balance < FREEZE_PRICE_CREDITS:
        blocked_by = "insufficient_credits"

    return FreezeQuote(
        price=FREEZE_PRICE_CREDITS,
        balance=balance,
        held=held,
        max_held=MAX_FREEZES_HELD,
        purchases_this_week=bought,
        max_per_week=MAX_PURCHASES_PER_WEEK,
        can_buy=blocked_by is None,
        blocked_by=blocked_by,
    )


async def _already_charged(db: AsyncSession, user_id: uuid.UUID, request_id: str) -> bool:
    result = await db.execute(
        select(CreditLedger.id)
        .where(
            CreditLedger.user_id == user_id,
            CreditLedger.reason == CreditReasonEnum.SPEND_FREEZE.value,
            CreditLedger.ref_id == request_id,
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def buy(
    db: AsyncSession,
    user: User,
    request_id: uuid.UUID,
    now: datetime | None = None,
) -> tuple[FreezeQuote, bool]:
    """Compra un comodín. Devuelve (estado tras la compra, ¿era un reintento?).

    Lanza `FreezePurchaseError` si un tope o el saldo lo impiden. No hace commit:
    lo hace el endpoint, para que cargo y comodín entren en la misma transacción.
    """
    now = now or datetime.now(UTC)
    rid = str(request_id)

    locked = await db.execute(
        select(User).where(User.id == user.id).with_for_update().execution_options(populate_existing=True)
    )
    user = locked.scalar_one()

    if await _already_charged(db, user.id, rid):
        return await quote(db, user, now), True

    q = await quote(db, user, now)
    if q.blocked_by is not None:
        raise FreezePurchaseError(q.blocked_by)

    paid = await CreditsService.spend_fifo(
        db,
        user.id,
        FREEZE_PRICE_CREDITS,
        reason=CreditReasonEnum.SPEND_FREEZE.value,
        ref_type=_ref_type(now),
        ref_id=rid,
    )
    if not paid:  # el saldo cambió entre la cotización y el cargo
        raise FreezePurchaseError("insufficient_credits")

    user.streak_freeze_available += 1
    await db.flush()
    return await quote(db, user, now), False
