"""Tests for economy services."""

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.economy import CreditLedger, Referral
from app.services.economy import CreditsService, ReferralService


@pytest.mark.asyncio
async def test_grant_credits_idempotent(db_session: AsyncSession):
    """Test that granting credits with same idempotency key doesn't double-count."""
    user_id = uuid4()
    
    lot1 = await CreditsService.grant_credits(
        db_session, user_id, 100, "test", expires_in_days=90
    )
    await db_session.flush()
    
    lot2 = await CreditsService.grant_credits(
        db_session, user_id, 100, "test", expires_in_days=90
    )
    await db_session.flush()
    
    # Should return the same lot due to idempotency
    assert lot1.id == lot2.id


@pytest.mark.asyncio
async def test_credit_balance_never_negative(db_session: AsyncSession):
    """Test that balance calculation never returns negative."""
    user_id = uuid4()
    
    # Grant 100 credits
    await CreditsService.grant_credits(db_session, user_id, 100, "grant", expires_in_days=90)
    
    # Try to spend 150 (more than available)
    success = await CreditsService.spend_fifo(db_session, user_id, 150, "spend")
    assert success is False
    
    balance = await CreditsService.get_balance(db_session, user_id)
    assert balance == 100  # Unchanged


@pytest.mark.asyncio
async def test_fifo_spending(db_session: AsyncSession):
    """Gastar consume primero el lote que caduca antes, no el que se creo antes.

    El saldo final (40) sale igual se consuma el lote que se consuma, asi que
    comprobarlo NO prueba FIFO: este test pasaba con el orden invertido, y las
    dos variables `lot1`/`lot2` se creaban sin que nadie las mirara (lo delato
    ruff con F841 el 2026-09-20). Lo que si lo prueba es a que lote apunta cada
    cargo: el ledger es inmutable y gastar nace como una fila negativa con
    `lot_id` apuntando al lote consumido.
    """
    user_id = uuid4()

    # Lote 1: creado ANTES, pero caduca DESPUES (100 dias).
    lot1 = await CreditsService.grant_credits(
        db_session, user_id, 50, "grant1", expires_in_days=100
    )
    await db_session.flush()

    # Lote 2: creado DESPUES, pero caduca ANTES (50 dias) -> se gasta primero.
    lot2 = await CreditsService.grant_credits(
        db_session, user_id, 50, "grant2", expires_in_days=50
    )
    await db_session.flush()

    success = await CreditsService.spend_fifo(db_session, user_id, 60, "spend_test")
    assert success is True

    balance = await CreditsService.get_balance(db_session, user_id)
    assert balance == 40  # 100 concedidos - 60 gastados

    cargos = (
        await db_session.execute(
            select(CreditLedger.lot_id, CreditLedger.amount).where(
                CreditLedger.user_id == user_id, CreditLedger.amount < 0
            )
        )
    ).all()
    assert cargos, "gastar no dejo ninguna fila negativa en el ledger"

    gastado: dict[int | None, int] = {}
    for lot_id, amount in cargos:
        gastado[lot_id] = gastado.get(lot_id, 0) + amount

    assert gastado.get(lot2.id) == -50, (
        f"el lote que caduca antes (lot2) tenia que agotarse entero: "
        f"esperaba -50, salio {gastado.get(lot2.id)!r}. Reparto completo: {gastado!r}"
    )
    assert gastado.get(lot1.id) == -10, (
        f"del lote que caduca despues (lot1) solo tenian que salir 10: "
        f"esperaba -10, salio {gastado.get(lot1.id)!r}. Reparto completo: {gastado!r}"
    )


@pytest.mark.asyncio
async def test_referral_code_generation(db_session: AsyncSession):
    """Test that referral codes are generated uniquely."""
    user1_id = uuid4()
    user2_id = uuid4()
    
    code1 = await ReferralService.get_or_create_referral_code(db_session, user1_id)
    code2 = await ReferralService.get_or_create_referral_code(db_session, user2_id)
    await db_session.flush()
    
    # Should get the same code on re-request
    code1_again = await ReferralService.get_or_create_referral_code(db_session, user1_id)
    assert code1 == code1_again
    
    # Different users should get different codes
    assert code1 != code2


@pytest.mark.asyncio
async def test_referral_activation(db_session: AsyncSession):
    """Test referral activation flow."""
    referrer_id = uuid4()
    referred_id = uuid4()
    
    # Create referral code
    code = await ReferralService.get_or_create_referral_code(db_session, referrer_id)
    await db_session.flush()
    
    # Register referral
    result = await ReferralService.register_referral(db_session, code, referred_id)
    assert result == referrer_id
    await db_session.flush()
    
    # Check referral is pending
    result = await db_session.execute(
        select(Referral).where(Referral.referred_id == referred_id)
    )
    referral = result.scalar()
    assert referral.status == "pending"
    
    # Activate referral
    success = await ReferralService.activate_referral(db_session, referred_id)
    assert success is True
    await db_session.flush()
    
    # Check referral is now activated
    result = await db_session.execute(
        select(Referral).where(Referral.referred_id == referred_id)
    )
    referral = result.scalar()
    assert referral.status == "activated"
    assert referral.activated_at is not None


@pytest.mark.asyncio
async def test_expired_credits_not_counted(db_session: AsyncSession):
    """Test that expired credits are not included in balance."""
    user_id = uuid4()
    
    # Grant credits that already expired
    await CreditsService.grant_credits(
        db_session, user_id, 100, "grant", expires_in_days=-1
    )
    await db_session.flush()
    
    balance = await CreditsService.get_balance(db_session, user_id)
    assert balance == 0  # Expired credits not counted
