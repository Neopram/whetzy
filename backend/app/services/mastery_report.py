"""Informe de dominio comprado con créditos (ECONOMIA §2.3: 300, «compartible con
empleadores»).

Es el segundo sumidero cableado, después del comodín de racha. La economía se
diseña desde los sumideros (§2.1); con los grifos de aprendizaje abiertos el
2026-10-02, sin un sitio donde gastar los créditos se acumulan hasta caducar.

El informe es una **instantánea**: se copia al comprarlo y la página pública
la lee tal cual, como un certificado. Lleva lo que ya enseña la app (dominio
por ruta, skills dominadas, precisión, racha máxima) y el nombre público del
usuario; nada de email ni de identificadores internos.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.economy import CreditReasonEnum, MasteryReport
from app.models.user import User
from app.services.economy import CreditsService

MASTERY_REPORT_PRICE = 300
# Por ruta, como mucho tantas skills dominadas con nombre: el informe se lee en
# una pantalla y se imprime en una o dos hojas.
MAX_SKILLS_LISTED = 12


class InsufficientCredits(Exception):
    pass


async def build_snapshot(db: AsyncSession, user: User, now: datetime) -> dict[str, object]:
    from app.services.progress import get_dashboard, get_skill_breakdown

    dashboard = await get_dashboard(db, user)
    tracks = []
    for t in dashboard.tracks:
        if t.average_mastery <= 0:
            continue
        mastered = [s for s in await get_skill_breakdown(db, user, track_id=t.track_id) if s.mastered]
        mastered.sort(key=lambda s: -s.p_known)
        tracks.append(
            {
                "track_id": t.track_id,
                "name_es": t.name_es,
                "name_en": t.name_en,
                "icon": t.icon,
                "average_mastery": t.average_mastery,
                "skills_mastered": t.skills_mastered,
                "total_skills": t.total_skills,
                "mastered_skills": [
                    {"name_es": s.name_es, "name_en": s.name_en, "p_known": s.p_known}
                    for s in mastered[:MAX_SKILLS_LISTED]
                ],
            }
        )
    tracks.sort(key=lambda t: -float(t["average_mastery"]))  # type: ignore[arg-type]
    return {
        "generated_at": now.isoformat(),
        "display_name": user.display_name,
        "username": user.username,
        "total_questions_answered": dashboard.total_questions_answered,
        "overall_accuracy": dashboard.overall_accuracy,
        "max_streak": dashboard.max_streak,
        "tracks": tracks,
    }


async def buy(db: AsyncSession, user: User, request_id: str, now: datetime | None = None) -> MasteryReport:
    """Cobra 300 créditos y guarda el informe. El mismo `request_id` devuelve el
    informe ya comprado sin cobrar otra vez. Lanza InsufficientCredits."""
    now = now or datetime.now(UTC)
    if db.bind.dialect.name == "postgresql":
        # Serializa las compras de un usuario: dos peticiones con el mismo
        # request_id verían «no existe» a la vez y cobrarían las dos.
        await db.execute(select(User.id).where(User.id == user.id).with_for_update())
    existing = (
        await db.execute(
            select(MasteryReport).where(MasteryReport.request_id == request_id, MasteryReport.user_id == user.id)
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    paid = await CreditsService.spend_fifo(
        db, user.id, MASTERY_REPORT_PRICE, CreditReasonEnum.SPEND_REPORT.value,
        ref_type="mastery_report", ref_id=request_id,
    )
    if not paid:
        raise InsufficientCredits
    report = MasteryReport(
        code=secrets.token_hex(16),
        user_id=user.id,
        request_id=request_id,
        snapshot=await build_snapshot(db, user, now),
        created_at=now,
    )
    db.add(report)
    await db.flush()
    return report
