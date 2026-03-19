#!/bin/sh
set -eu

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
