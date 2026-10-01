"""Seeds gamification reference data (leagues, daily-mission templates, badges).

Idempotent: upserts by primary key. Run standalone with
`python -m app.services.seed`, or import `seed_gamification` and call it
after `load_content` on deploy.
"""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import AsyncSessionLocal, init_db
from app.models.gamification import Badge, League, Mission

LEAGUES: list[dict[str, Any]] = [
    {"id": "bronze", "name": "Bronce", "tier": "bronze", "min_xp": 0},
    {"id": "silver", "name": "Plata", "tier": "silver", "min_xp": 500},
    {"id": "gold", "name": "Oro", "tier": "gold", "min_xp": 2000},
    {"id": "platinum", "name": "Platino", "tier": "platinum", "min_xp": 5000},
    {"id": "diamond", "name": "Diamante", "tier": "diamond", "min_xp": 10000},
]

# Mission `type` MUST be one of the values apply_quiz_event handles:
# questions_answered | correct_answers | xp_earned | perfect_combo.
# The service picks the first 3 by id, so ids are prefixed to control the mix.
MISSIONS: list[dict[str, Any]] = [
    {"id": "m1_questions", "type": "questions_answered", "target_value": 10, "xp_reward": 30,
     "name_es": "Responde 10 preguntas", "name_en": "Answer 10 questions"},
    {"id": "m2_correct", "type": "correct_answers", "target_value": 8, "xp_reward": 25,
     "name_es": "Acierta 8 preguntas", "name_en": "Get 8 correct"},
    {"id": "m3_combo", "type": "perfect_combo", "target_value": 5, "xp_reward": 20,
     "name_es": "Consigue un combo de 5", "name_en": "Reach a 5-combo"},
    {"id": "m4_xp", "type": "xp_earned", "target_value": 100, "xp_reward": 15,
     "name_es": "Gana 100 XP", "name_en": "Earn 100 XP"},
]

BADGES: list[dict[str, Any]] = [
    {"id": "streak_7", "name_es": "Racha de 7", "name_en": "7-day Streak", "icon": "🔥",
     "description_es": "Estudia 7 días seguidos", "description_en": "Study 7 days in a row",
     "criteria_type": "streak", "criteria_value": 7},
    {"id": "streak_30", "name_es": "Racha de 30", "name_en": "30-day Streak", "icon": "🌋",
     "description_es": "Estudia 30 días seguidos", "description_en": "Study 30 days in a row",
     "criteria_type": "streak", "criteria_value": 30},
    {"id": "questions_100", "name_es": "Centurión", "name_en": "Centurion", "icon": "💯",
     "description_es": "Responde 100 preguntas", "description_en": "Answer 100 questions",
     "criteria_type": "questions_answered", "criteria_value": 100},
    {"id": "xp_1000", "name_es": "Mil XP", "name_en": "One Thousand XP", "icon": "⚡",
     "description_es": "Acumula 1000 XP", "description_en": "Accumulate 1000 XP",
     "criteria_type": "total_xp", "criteria_value": 1000},
    {"id": "xp_10000", "name_es": "Leyenda", "name_en": "Legend", "icon": "👑",
     "description_es": "Acumula 10000 XP", "description_en": "Accumulate 10000 XP",
     "criteria_type": "total_xp", "criteria_value": 10000},
    {"id": "first_mastery", "name_es": "Primer Dominio", "name_en": "First Mastery", "icon": "🎯",
     "description_es": "Domina tu primera habilidad", "description_en": "Master your first skill",
     "criteria_type": "skills_mastered", "criteria_value": 1},
    {"id": "level_10", "name_es": "Nivel 10", "name_en": "Level 10", "icon": "🚀",
     "description_es": "Alcanza el nivel 10", "description_en": "Reach level 10",
     "criteria_type": "level", "criteria_value": 10},
    {"id": "perfectionist", "name_es": "Perfeccionista", "name_en": "Perfectionist", "icon": "🌟",
     "description_es": "Sesión perfecta 10/10", "description_en": "Perfect 10/10 session",
     "criteria_type": "perfect_session", "criteria_value": 1},
    {"id": "ambassador", "name_es": "Embajador", "name_en": "Ambassador", "icon": "🤝",
     "description_es": "25 amigos invitados que se activaron", "description_en": "25 invited friends who activated",
     "criteria_type": "referrals_credited", "criteria_value": 25},
]


async def seed_gamification(db: AsyncSession) -> dict[str, Any]:
    for data in LEAGUES:
        league = await db.get(League, data["id"])
        if league is None:
            league = League(id=data["id"])
            db.add(league)
        league.name, league.tier, league.min_xp = data["name"], data["tier"], data["min_xp"]

    for data in MISSIONS:
        mission = await db.get(Mission, data["id"])
        if mission is None:
            mission = Mission(id=data["id"])
            db.add(mission)
        for k, v in data.items():
            if k != "id":
                setattr(mission, k, v)

    for data in BADGES:
        badge = await db.get(Badge, data["id"])
        if badge is None:
            badge = Badge(id=data["id"])
            db.add(badge)
        for k, v in data.items():
            if k != "id":
                setattr(badge, k, v)

    await db.commit()
    return {"leagues": len(LEAGUES), "missions": len(MISSIONS), "badges": len(BADGES)}


async def main() -> None:
    # Igual que content_loader.main: `create_all` solo en desarrollo. En produccion
    # el esquema es de Alembic, y `create_all` ya tumbo el arranque el 2026-09-20.
    if settings.ENVIRONMENT == "development":
        await init_db()
    async with AsyncSessionLocal() as db:
        stats = await seed_gamification(db)
    print(f"Gamification seeded: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
