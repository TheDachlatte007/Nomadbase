from __future__ import annotations

import asyncio
import os
import subprocess
from typing import Final

import asyncpg
from sqlalchemy import func, select

from app.db import async_session_maker, engine
from app.models.place import Place
from app.seed_alpha import seed_alpha_places


DATABASE_URL: Final[str] = os.environ["DATABASE_URL"]
RAW_DATABASE_URL: Final[str] = DATABASE_URL.replace("+asyncpg", "")
MAX_DB_WAIT_ATTEMPTS: Final[int] = 30
DB_WAIT_SECONDS: Final[int] = 2


async def wait_for_database() -> None:
    for attempt in range(1, MAX_DB_WAIT_ATTEMPTS + 1):
        try:
            conn = await asyncpg.connect(RAW_DATABASE_URL)
            try:
                await conn.execute("SELECT 1")
            finally:
                await conn.close()
            print("Database is reachable")
            return
        except Exception as exc:
            print(f"Database not ready yet ({attempt}/{MAX_DB_WAIT_ATTEMPTS}): {exc}")
            await asyncio.sleep(DB_WAIT_SECONDS)

    raise SystemExit("Database did not become reachable in time")


async def repair_partial_schema() -> None:
    conn = await asyncpg.connect(RAW_DATABASE_URL)
    try:
        has_alembic = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version')"
        )
        has_places = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'places')"
        )

        if not has_alembic and has_places:
            print(
                "Detected partially initialized schema without alembic_version; resetting public schema..."
            )
            await conn.execute("DROP SCHEMA public CASCADE")
            await conn.execute("CREATE SCHEMA public")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    finally:
        await conn.close()


def run_migrations() -> None:
    print("Running migrations...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)


async def seed_if_needed() -> None:
    print("Checking if places table is empty...")
    async with async_session_maker() as session:
        count = (
            await session.execute(select(func.count()).select_from(Place))
        ).scalar_one()

    print(f"Places in DB: {count}")
    if count == 0:
        print("No places found - running first-boot seed...")
        inserted = await seed_alpha_places()
        print(f"First-boot seed complete: {inserted} places")


async def bootstrap() -> None:
    print("Waiting for database...")
    await wait_for_database()
    print("Checking for partial bootstrap state...")
    await repair_partial_schema()
    run_migrations()
    await seed_if_needed()
    await engine.dispose()


def main() -> None:
    asyncio.run(bootstrap())


if __name__ == "__main__":
    main()
