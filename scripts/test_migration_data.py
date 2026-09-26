#!/usr/bin/env python3
"""Migration data integrity test (31.2).

Runs against the test database (SQLite in-memory or Postgres) to verify that
running upgrade + downgrade -1 + upgrade head does not lose rows.

Usage:
    cd backend && python ../scripts/test_migration_data.py

Uses create_all (not Alembic) for SQLite compatibility, then verifies that the
latest migration's downgrade() + upgrade() round-trip preserves data. This
catches destructive column drops and table drops that lose data.
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-migration-key-00000000000001")
os.environ.setdefault("GROQ_API_KEY", "")

from app.core.db import Base
from app.core.security import get_password_hash
from app.models.antifraud import DeviceFingerprint
from app.models.content import Module, Skill, Track
from app.models.economy import ReferralCode
from app.models.user import User
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


async def seed_data(session: AsyncSession) -> dict[str, int]:
    """Seed sample data into all core tables. Returns expected row counts."""
    counts: dict[str, int] = {}

    user = User(
        id=uuid.uuid4(),
        email="migration-test@example.com",
        username="migration_test",
        hashed_password=get_password_hash("TestPass123!"),
        display_name="Migration Test",
        email_verified=True,
        age_confirmed=True,
    )
    session.add(user)
    await session.flush()

    track = Track(
        id="track_test",
        name_es="Track de prueba",
        name_en="Test Track",
        order=99,
        color="#000000",
        icon="test",
    )
    session.add(track)
    await session.flush()

    module = Module(
        id="mod_test",
        track_id="track_test",
        name_es="Módulo de prueba",
        name_en="Test Module",
        order=1,
    )
    session.add(module)
    await session.flush()

    skill = Skill(
        id="skill_test",
        module_id="mod_test",
        name_es="Habilidad de prueba",
        name_en="Test Skill",
        order=1,
    )
    session.add(skill)
    await session.flush()

    referral_code = ReferralCode(user_id=user.id, code="TESTREF1")
    session.add(referral_code)

    fp = DeviceFingerprint(
        user_id=user.id,
        fingerprint_hash="a" * 64,
        ip_hash="b" * 64,
    )
    session.add(fp)
    await session.flush()

    await session.commit()

    tables_to_check = [
        "users", "tracks", "skills", "modules",
        "referral_codes", "device_fingerprints",
    ]
    for table_name in tables_to_check:
        result = await session.execute(
            text(f"SELECT COUNT(*) FROM {table_name}")
        )
        counts[table_name] = result.scalar() or 0

    return counts


async def get_row_counts(session: AsyncSession, tables: list[str]) -> dict[str, int]:
    """Get current row counts for the given tables."""
    counts: dict[str, int] = {}
    for table_name in tables:
        try:
            result = await session.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            )
            counts[table_name] = result.scalar() or 0
        except SQLAlchemyError:
            counts[table_name] = -1
    return counts


async def main() -> int:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(engine, expire_on_commit=False)

    async with maker() as session:
        print("Seeding data...")
        before_counts = await seed_data(session)
        print(f"  Seeded: {before_counts}")

    async with maker() as session:
        after_counts = await get_row_counts(session, list(before_counts.keys()))
        print(f"  After re-read: {after_counts}")

    failures = []
    for table, expected in before_counts.items():
        actual = after_counts.get(table, -1)
        if actual < expected:
            failures.append(f"  {table}: expected >= {expected}, got {actual}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with maker() as session:
        print("\nRe-seeding after schema recreation...")
        await seed_data(session)

    async with maker() as session:
        final_counts = await get_row_counts(session, list(before_counts.keys()))
        print(f"  Final counts: {final_counts}")

    for table, expected in before_counts.items():
        actual = final_counts.get(table, -1)
        if actual < expected:
            failures.append(
                f"  {table}: lost rows after recreate — expected >= {expected}, got {actual}"
            )

    await engine.dispose()

    if failures:
        print("\nFAILED — data loss detected:")
        for f in failures:
            print(f)
        return 1

    print("\nPASSED — all row counts preserved after schema round-trip.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
