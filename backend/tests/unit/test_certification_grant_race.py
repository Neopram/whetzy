"""certification.grant bajo entrega duplicada concurrente (S.7).

Un reintento de Paddle del mismo webhook de compra puede llegar mientras el
primero todavía no ha hecho commit: el `SELECT` de `purchase_for` no ve
todavía la fila que el otro está insertando, así que los dos la dan por no
comprada y los dos intentan el `INSERT`. Sin una red de seguridad contra la
unique constraint, el segundo se iba abajo con un `IntegrityError` sin
capturar en vez de devolver silenciosamente el derecho ya concedido.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Track
from app.models.exam import CertificationPurchase
from app.services import certification


@pytest.mark.asyncio
async def test_grant_survives_a_row_inserted_between_its_own_check_and_insert(
    db_session: AsyncSession, user, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_session.add(Track(id="trkRACE", name_es="C", name_en="C", order=94, is_certification=True))
    await db_session.commit()

    winner = CertificationPurchase(
        id=uuid.uuid4(),
        user_id=user.id,
        track_id="trkRACE",
        price_usd=39.99,
        source="paddle",
        external_ref="txn_winner",
    )
    db_session.add(winner)
    await db_session.commit()

    real_purchase_for = certification.purchase_for
    calls = {"n": 0}

    async def lying_once(db: AsyncSession, user_id: uuid.UUID, track_id: str):
        calls["n"] += 1
        if calls["n"] == 1:
            return None  # simula el SELECT que no vio todavía la fila ganadora
        return await real_purchase_for(db, user_id, track_id)

    monkeypatch.setattr(certification, "purchase_for", lying_once)

    result = await certification.grant(
        db_session, user.id, "trkRACE", source="paddle", external_ref="txn_loser"
    )

    assert result.external_ref == "txn_winner"  # la que de verdad ganó la carrera
    rows = (
        await db_session.execute(
            select(CertificationPurchase).where(
                CertificationPurchase.user_id == user.id, CertificationPurchase.track_id == "trkRACE"
            )
        )
    ).scalars().all()
    assert len(rows) == 1
