# Deploy Notes

## Current target

This repository is prepared for a first private deployment through GitHub and Portainer.

## Services

- `db`: PostgreSQL 16 with PostGIS 3.4
- `app`: single FastAPI container that serves both the API and the built Vue frontend on port `8000`

## Required environment

None for the current alpha stack.

The bundled Postgres service is configured for passwordless local alpha deployment so the stack can boot without extra setup.

Optional hardening envs are now available if you expose the app beyond a throwaway LAN test:

- `CORS_ALLOW_ORIGINS`
- `TRUSTED_HOSTS`
- `ENABLE_GZIP`
- `IMPORT_AUTO_QUEUE_ON_CITY_CREATE`

For example, a homeserver deploy can move from `*` to your real hostnames once the first stack is stable.

## Expected first-run behavior

The app container runs:

1. `alembic upgrade head`
2. `python -m app.seed_alpha` when `SEED_ALPHA_DATA=true`
3. `uvicorn app.main:app --host 0.0.0.0 --port 8000`

That means the database schema should be created automatically on first deploy once the database is reachable.

If you previously deployed with an older password-protected Postgres volume, this compose file now uses a fresh volume automatically.

Old stacks may still leave behind a `nomadbase_pgdata` volume in Docker, but the current setup now boots against the new `nomadbase_postgres_data` volume instead.

## First checks after deploy

Open:

- `/`
- `/api/health`
- `/api/docs`

The homepage should be served directly by the FastAPI app container.
The map tab should render alpha sample places right away after a healthy first boot.

## Quick smoke check

After deploy, you can run:

```powershell
python scripts/smoke_check.py http://YOUR-HOST:PORT
```

This checks the homepage plus the core alpha endpoints:

- `/`
- `/api/health`
- `/api/map/places?limit=1`
- `/api/trips/`
- `/api/saves/`
- `/api/tracking/expenses`
- `/api/tracking/expenses/summary`
- `/api/admin/status`
- `/api/admin/imports`
- `/api/admin/import-jobs`
- `/api/docs`

## Trip baseline check

For a real trip-prep flow, the first useful manual check is now:

1. open `Trips`
2. create one trip with 2-3 cities
3. open the trip planner
4. use `Import missing stops` if any city shows `thin` or `missing`
   or `Prep weak stops` if the route looks stale or misses key trip categories
5. wait for the background jobs to finish in Admin or on the planner
6. confirm the map and planner start showing local suggestions for each stop

Cities now also show whether they still miss core route categories:

- `food`
- `stay`
- `essentials`
- `transport`

This matters because a city with many POIs can still feel weak for a real trip if it lacks basics like transport anchors or day-to-day places.

## Known limitations

- The project still needs real deployment verification because Docker was not runnable in this IDE session.
- `trips`, `tracking`, and `admin` are functional alpha flows, but not yet hardened production features.
