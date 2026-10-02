"""Créditos por aprender (ECONOMIA §2.2): los grifos que no son referidos ni códigos.

Hasta el 2026-10-02 ninguno abonaba nada: `grant_credits` solo lo llamaban el
código promocional y el programa de referidos (ADR-57). Aquí se calculan a
partir del estado real, no de lo que diga el cliente, y cada abono lleva una
clave de idempotencia propia del logro, así que llamar a `award_learning_credits`
dos veces, o desde dos sitios a la vez, no paga dos veces.

Cableados:

| Logro | Créditos | Clave (una vez por…) |
|---|---|---|
| Diagnóstico inicial | 50 | usuario |
| Módulo con **todas** sus skills ≥ 0,8 | 100 | módulo |
| Skill saltada con un test-out aprobado y dominio ≥ 0,8 | 50, máx. 500/mes | skill |
| Racha ≥ 7 días | 70 | semana ISO |
| Racha ≥ 30 días | 300 | mes |

Tope global: **1.500 créditos al mes** por aprendizaje. Lo que no cabe no se
paga a medias: se queda para el mes siguiente si su clave sigue valiendo (un
módulo, una skill); la racha de una semana o un mes ya pasados no vuelve.

No cableados, a propósito:

- **Proyecto entregado con tests verdes (200).** `POST /projects/{slug}/submit-step`
  marca el paso con `passed` que manda el navegador; pagar por eso sería pagar
  por una afirmación del cliente. Entra cuando el backend verifique los tests.
- **Simulacro aprobado (150).** El simulacro no tiene nota de corte a propósito
  (`services/mock_exam.py`: la escala real de cada certificación no es
  reproducible), así que «aprobado» no es un hecho que podamos comprobar.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Skill
from app.models.economy import CreditLedger, CreditReasonEnum
from app.models.exam import MockExamAttempt
from app.models.user import User, UserSkillState

DIAGNOSTIC_CREDITS = 50
MODULE_CREDITS = 100
MODULE_SKILL_MASTERY = 0.8
SKILL_SKIPPED_CREDITS = 50
SKILL_SKIPPED_MONTHLY_CAP = 500
STREAK_7_CREDITS = 70
STREAK_30_CREDITS = 300
LEARNING_MONTHLY_CAP = 1500
LOT_LIFETIME = timedelta(days=90)  # como cualquier lote (§2.4)

LEARNING_REASONS = (
    CreditReasonEnum.ONBOARDING_BONUS.value,
    CreditReasonEnum.MODULE_DONE.value,
    CreditReasonEnum.SKILL_SKIPPED.value,
    CreditReasonEnum.STREAK_7.value,
    CreditReasonEnum.STREAK_30.value,
)


def _month_start(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


async def _earned_this_month(
    db: AsyncSession, user_id: uuid.UUID, reasons: Iterable[str], now: datetime
) -> int:
    total = await db.scalar(
        select(func.coalesce(func.sum(CreditLedger.amount), 0)).where(
            CreditLedger.user_id == user_id,
            CreditLedger.amount > 0,
            CreditLedger.reason.in_(list(reasons)),
            CreditLedger.created_at >= _month_start(now),
        )
    )
    return int(total or 0)


async def _already(db: AsyncSession, key: str) -> bool:
    return (
        await db.scalar(select(CreditLedger.id).where(CreditLedger.idempotency_key == key))
    ) is not None


async def _completed_modules(db: AsyncSession, user_id: uuid.UUID) -> list[str]:
    """Módulos con todas sus skills a ≥ 0,8 (la regla del §2.2, más estricta que
    la media con la que la app pinta un módulo como superado)."""
    rows = await db.execute(
        select(Skill.module_id, func.count(Skill.id), func.count(UserSkillState.skill_id))
        .outerjoin(
            UserSkillState,
            (UserSkillState.skill_id == Skill.id)
            & (UserSkillState.user_id == user_id)
            & (UserSkillState.p_known >= MODULE_SKILL_MASTERY),
        )
        .where(
            Skill.module_id.in_(
                select(Skill.module_id)
                .join(UserSkillState, UserSkillState.skill_id == Skill.id)
                .where(UserSkillState.user_id == user_id)
            )
        )
        .group_by(Skill.module_id)
    )
    return sorted(str(module_id) for module_id, total, mastered in rows.all() if total and mastered == total)


async def _skipped_skills(db: AsyncSession, user_id: uuid.UUID) -> list[str]:
    """Skills de módulos con un test-out aprobado a tiempo y dominio ≥ 0,8 hoy."""
    attempts = (
        await db.scalars(
            select(MockExamAttempt).where(
                MockExamAttempt.user_id == user_id,
                MockExamAttempt.kind == "test_out",
                MockExamAttempt.status == "submitted",
            )
        )
    ).all()
    modules = {a.module_id for a in attempts if a.module_id and (a.report or {}).get("passed") is True}
    if not modules:
        return []
    rows = await db.execute(
        select(Skill.id)
        .join(UserSkillState, UserSkillState.skill_id == Skill.id)
        .where(
            Skill.module_id.in_(modules),
            UserSkillState.user_id == user_id,
            UserSkillState.p_known >= MODULE_SKILL_MASTERY,
        )
    )
    return sorted(str(skill_id) for skill_id in rows.scalars().all())


async def award_learning_credits(
    db: AsyncSession, user: User, now: datetime | None = None
) -> int:
    """Abona lo que `user` ha ganado aprendiendo y aún no se le ha pagado.

    Hace `flush`, no `commit`: lo decide quien llama. Returns los créditos abonados.
    """
    from app.services.economy import ReferralService

    now = now or datetime.now(UTC)
    if db.bind.dialect.name == "postgresql":
        # Dos llamadas a la vez (fin de sesión y vuelta horaria) leerían el mismo
        # «ganado este mes» y podrían pasarse del tope juntas.
        await db.execute(select(User.id).where(User.id == user.id).with_for_update())

    year, week, _ = now.isocalendar()
    candidates: list[tuple[str, int, str, str | None]] = []  # (reason, credits, key, ref_id)
    if await ReferralService.diagnostic_done(db, user):
        candidates.append(
            (CreditReasonEnum.ONBOARDING_BONUS.value, DIAGNOSTIC_CREDITS, f"learn:diagnostic:{user.id}", None)
        )
    for module_id in await _completed_modules(db, user.id):
        candidates.append(
            (CreditReasonEnum.MODULE_DONE.value, MODULE_CREDITS, f"learn:module:{user.id}:{module_id}", module_id)
        )
    for skill_id in await _skipped_skills(db, user.id):
        candidates.append(
            (CreditReasonEnum.SKILL_SKIPPED.value, SKILL_SKIPPED_CREDITS, f"learn:skill_skipped:{user.id}:{skill_id}", skill_id)
        )
    if user.current_streak >= 7:
        candidates.append(
            (CreditReasonEnum.STREAK_7.value, STREAK_7_CREDITS, f"learn:streak7:{user.id}:{year}-W{week:02d}", None)
        )
    if user.current_streak >= 30:
        candidates.append(
            (CreditReasonEnum.STREAK_30.value, STREAK_30_CREDITS, f"learn:streak30:{user.id}:{now:%Y-%m}", None)
        )

    room = LEARNING_MONTHLY_CAP - await _earned_this_month(db, user.id, LEARNING_REASONS, now)
    skipped_room = SKILL_SKIPPED_MONTHLY_CAP - await _earned_this_month(
        db, user.id, (CreditReasonEnum.SKILL_SKIPPED.value,), now
    )
    granted = 0
    for reason, credits, key, ref_id in candidates:
        if credits > room or (reason == CreditReasonEnum.SKILL_SKIPPED.value and credits > skipped_room):
            continue
        if await _already(db, key):
            continue
        try:
            async with db.begin_nested():
                db.add(
                    CreditLedger(
                        user_id=user.id,
                        amount=credits,
                        reason=reason,
                        ref_type="learning",
                        ref_id=ref_id,
                        idempotency_key=key,
                        created_at=now,
                        expires_at=now + LOT_LIFETIME,
                    )
                )
        except IntegrityError:  # otra llamada lo abonó entre medias
            continue
        room -= credits
        if reason == CreditReasonEnum.SKILL_SKIPPED.value:
            skipped_room -= credits
        granted += credits
    return granted


async def award_recently_active(db: AsyncSession, now: datetime | None = None) -> int:
    """Vuelta horaria: lo que no haya abonado el fin de sesión (una pestaña
    cerrada sin `/quiz/end`, una racha que cruzó la semana). Solo quien ha
    estudiado en las últimas 26 h, que es quien puede haber ganado algo."""
    now = now or datetime.now(UTC)
    users = (
        await db.scalars(
            select(User).where(User.is_active.is_(True), User.last_active >= now - timedelta(hours=26))
        )
    ).all()
    total = 0
    for user in users:
        total += await award_learning_credits(db, user, now)
    await db.flush()
    return total
