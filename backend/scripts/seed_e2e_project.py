"""Siembra un proyecto SQL de dos pasos para `e2e/proyectos.spec.ts` (43.6).

El catálogo no trae proyectos (0 en `content/`; ADR-62 congela el contenido
nuevo) y `content_loader` no los carga, así que el E2E crea el suyo. Idempotente:
borra y vuelve a crear el proyecto `e2e-sql-mascotas` con sus pasos (las
entregas caen en cascada). Solo para bases locales y de CI; se niega a correr
con ENVIRONMENT=production.

    cd backend && python scripts/seed_e2e_project.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.models.project import Project, ProjectStep

SLUG = "e2e-sql-mascotas"
FAIL = "json('roto')"  # SQLite: error si la comprobación no se cumple
STEPS = [
    (
        "Crea la tabla", "Create the table",
        "CREATE TABLE pets(name TEXT, age INT); INSERT INTO pets VALUES ('Rex', 9), ('Mia', 2);",
        f"SELECT CASE WHEN (SELECT COUNT(*) FROM pets) = 2 THEN 1 ELSE {FAIL} END;",
    ),
    (
        "La mayor", "The oldest",
        "SELECT name FROM pets ORDER BY age DESC LIMIT 1;",
        (
            "SELECT CASE WHEN (SELECT name FROM pets ORDER BY age DESC LIMIT 1) = 'Rex' "
            f"THEN 1 ELSE {FAIL} END;"
        ),
    ),
]


async def main() -> None:
    if settings.ENVIRONMENT == "production":
        raise SystemExit("seed_e2e_project: no en producción")
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Project).where(Project.slug == SLUG))
        project = Project(
            id=uuid.uuid4(), slug=SLUG, track_id="track01", runtime="sql",
            name_es="Mascotas (E2E)", name_en="Pets (E2E)", difficulty=1, order=999,
        )
        db.add(project)
        for n, (title_es, title_en, solution, test) in enumerate(STEPS, start=1):
            db.add(
                ProjectStep(
                    id=uuid.uuid4(), project_id=project.id, step_number=n,
                    title_es=title_es, title_en=title_en,
                    starter_code=f"-- paso {n}", test_code=test, solution_code=solution,
                )
            )
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
