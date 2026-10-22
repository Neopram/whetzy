"""Ascenso y descenso reales entre ligas (decisión del dueño, 2026-10-21).

Hasta ahora la semana nueva copiaba la liga de la anterior: las zonas de ascenso
y descenso se pintaban pero nunca se aplicaban, y por eso la ceremonia de ascenso
estaba bloqueada (ADR-67, PLAN_UI_AVANZADA §6.2). Lo que se fija aquí:

- top 5 de una liga de ≥ 10 → sube un nivel; últimos 5 → baja uno; el resto se queda;
- con menos de 10 miembros no hay zonas, así que nadie se mueve;
- el nivel más alto no sube más y el más bajo no baja más;
- solo cuenta la semana inmediatamente anterior: quien vuelve tras semanas fuera
  retoma su liga;
- los empates no castigan: el rango es 1 + quienes sacaron estrictamente más XP;
- la clasificación devuelve el movimiento (`last_week_movement`) para que el
  cliente pueda contarlo.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import League, LeagueEntry
from app.models.user import User
from app.services.gamification.service import (
    get_current_standings,
    get_or_create_current_entry,
    week_start_of,
)

THIS_WEEK = week_start_of(date.today())
LAST_WEEK = THIS_WEEK - timedelta(weeks=1)


def _league(tier: str, min_xp: int) -> League:
    return League(
        id=f"lg_{tier}_{uuid.uuid4().hex[:6]}",
        name=tier.capitalize(),
        tier=tier,
        min_xp=min_xp,
    )


async def _tiers(db: AsyncSession) -> tuple[League, League, League]:
    bronze, silver, gold = (
        _league("bronze", 0),
        _league("silver", 100),
        _league("gold", 500),
    )
    db.add_all([bronze, silver, gold])
    await db.commit()
    return bronze, silver, gold


async def _last_week(
    db: AsyncSession, league: League, user: User, user_xp: int, others: list[int]
) -> None:
    """La semana pasada de `user` en `league`, con otros miembros que sacaron `others` XP."""
    for xp in others:
        other = User(
            id=uuid.uuid4(),
            email=f"o-{uuid.uuid4().hex[:8]}@test.com",
            username=f"o{uuid.uuid4().hex[:8]}",
            hashed_password="x",
            display_name="Otro",
        )
        db.add(other)
        await db.flush()
        db.add(
            LeagueEntry(
                user_id=other.id,
                league_id=league.id,
                week_start=LAST_WEEK,
                xp_earned=xp,
            )
        )
    db.add(
        LeagueEntry(
            user_id=user.id,
            league_id=league.id,
            week_start=LAST_WEEK,
            xp_earned=user_xp,
        )
    )
    await db.commit()


async def test_top_5_de_una_liga_de_10_sube(
    db_session: AsyncSession, user: User
) -> None:
    _, silver, gold = await _tiers(db_session)
    await _last_week(
        db_session, silver, user, 900, [10, 20, 30, 40, 50, 60, 70, 80, 90]
    )
    entry = await get_or_create_current_entry(db_session, user)
    assert entry is not None and entry.league_id == gold.id


async def test_ultimos_5_bajan(db_session: AsyncSession, user: User) -> None:
    bronze, silver, _ = await _tiers(db_session)
    await _last_week(db_session, silver, user, 1, [10, 20, 30, 40, 50, 60, 70, 80, 90])
    entry = await get_or_create_current_entry(db_session, user)
    assert entry is not None and entry.league_id == bronze.id


async def test_el_medio_se_queda(db_session: AsyncSession, user: User) -> None:
    # 12 miembros: rango 6 no está ni arriba (1-5) ni abajo (8-12).
    _, silver, _ = await _tiers(db_session)
    await _last_week(
        db_session, silver, user, 65, [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
    )
    entry = await get_or_create_current_entry(db_session, user)
    assert entry is not None and entry.league_id == silver.id


async def test_con_menos_de_10_nadie_se_mueve(
    db_session: AsyncSession, user: User
) -> None:
    _, silver, _ = await _tiers(db_session)
    await _last_week(db_session, silver, user, 900, [10, 20, 30])
    entry = await get_or_create_current_entry(db_session, user)
    assert entry is not None and entry.league_id == silver.id


async def test_el_nivel_mas_alto_no_sube_y_el_mas_bajo_no_baja(
    db_session: AsyncSession, user: User
) -> None:
    bronze, _, gold = await _tiers(db_session)
    await _last_week(db_session, gold, user, 900, [10, 20, 30, 40, 50, 60, 70, 80, 90])
    entry = await get_or_create_current_entry(db_session, user)
    assert entry is not None and entry.league_id == gold.id

    other = User(
        id=uuid.uuid4(),
        email=f"b-{uuid.uuid4().hex[:8]}@t.com",
        username=f"b{uuid.uuid4().hex[:8]}",
        hashed_password="x",
        display_name="B",
    )
    db_session.add(other)
    await db_session.commit()
    await _last_week(db_session, bronze, other, 0, [10, 20, 30, 40, 50, 60, 70, 80, 90])
    entry2 = await get_or_create_current_entry(db_session, other)
    assert entry2 is not None and entry2.league_id == bronze.id


async def test_solo_cuenta_la_semana_inmediatamente_anterior(
    db_session: AsyncSession, user: User
) -> None:
    _, silver, _ = await _tiers(db_session)
    old = LAST_WEEK - timedelta(weeks=2)
    db_session.add(
        LeagueEntry(user_id=user.id, league_id=silver.id, week_start=old, xp_earned=900)
    )
    await db_session.commit()
    entry = await get_or_create_current_entry(db_session, user)
    assert entry is not None and entry.league_id == silver.id


async def test_un_empate_en_la_frontera_no_castiga(
    db_session: AsyncSession, user: User
) -> None:
    # Cinco con 90 y el usuario también con 90: ninguno tiene a 5 por encima → todos suben.
    _, silver, gold = await _tiers(db_session)
    await _last_week(db_session, silver, user, 90, [90, 90, 90, 90, 90, 10, 20, 30, 40])
    entry = await get_or_create_current_entry(db_session, user)
    assert entry is not None and entry.league_id == gold.id


async def test_la_clasificacion_cuenta_el_movimiento(
    db_session: AsyncSession, user: User
) -> None:
    _, silver, gold = await _tiers(db_session)
    await _last_week(
        db_session, silver, user, 900, [10, 20, 30, 40, 50, 60, 70, 80, 90]
    )
    resp = await get_current_standings(db_session, user)
    assert resp is not None
    assert resp.league.id == gold.id
    assert resp.last_week_movement == "promoted"
