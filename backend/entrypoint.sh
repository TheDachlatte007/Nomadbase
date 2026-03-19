#!/bin/sh
set -eu

echo "Waiting for database..."
python - <<'PY'
import asyncio
import os
import sys

import asyncpg


DATABASE_URL = os.environ["DATABASE_URL"].replace("+asyncpg", "")


async def main():
    for attempt in range(30):
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            await conn.execute("SELECT 1")
            await conn.close()
            print("Database is reachable")
            return
        except Exception as exc:
            print(f"Database not ready yet ({attempt + 1}/30): {exc}")
            await asyncio.sleep(2)

    print("Database did not become reachable in time", file=sys.stderr)
    raise SystemExit(1)


asyncio.run(main())
PY

echo "Checking for partial bootstrap state..."
python - <<'PY'
import asyncio
import os

import asyncpg


DATABASE_URL = os.environ["DATABASE_URL"].replace("+asyncpg", "")


async def exists(conn, query, *args):
    return bool(await conn.fetchval(query, *args))


async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        has_alembic = await exists(
            conn,
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version')",
        )
        has_places = await exists(
            conn,
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'places')",
        )

        if not has_alembic and has_places:
            print("Detected partially initialized schema without alembic_version; resetting public schema...")
            await conn.execute("DROP SCHEMA public CASCADE")
            await conn.execute("CREATE SCHEMA public")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    finally:
        await conn.close()


asyncio.run(main())
PY

echo "Running migrations..."
alembic upgrade head

if [ "${SEED_ALPHA_DATA:-false}" = "true" ]; then
  echo "Seeding alpha sample data (SEED_ALPHA_DATA=true)..."
  python -m app.seed_alpha
else
  echo "Checking if places table is empty..."
  python -c "
import asyncio
from sqlalchemy import select, func
from app.db import async_session_maker
from app.models.place import Place

async def check():
    async with async_session_maker() as s:
        count = (await s.execute(select(func.count()).select_from(Place))).scalar_one()
        return count

count = asyncio.run(check())
print(f'Places in DB: {count}')
if count == 0:
    print('No places found - running first-boot seed...')
    import importlib, asyncio as a2
    seed = importlib.import_module('app.seed_alpha')
    inserted = a2.run(seed.seed_alpha_places())
    print(f'First-boot seed complete: {inserted} places')
"
fi

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
