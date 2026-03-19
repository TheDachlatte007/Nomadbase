# Deploy Notes

## Current target

This repository is prepared for a first private deployment through GitHub and Portainer.

## Services

- `db`: PostgreSQL 16 with PostGIS 3.4
- `api`: FastAPI backend on port `8000`
- `frontend`: static web shell with nginx proxy on port `80`

## Required environment

None for the current alpha stack.

The bundled Postgres service is configured for passwordless local alpha deployment so the stack can boot without extra setup.

## Expected first-run behavior

The API container runs:

1. `alembic upgrade head`
2. `python -m app.seed_alpha` when `SEED_ALPHA_DATA=true`
3. `uvicorn app.main:app --host 0.0.0.0 --port 8000`

That means the database schema should be created automatically on first deploy once the database is reachable.

If you previously deployed with a password-protected Postgres volume, this compose file now uses a fresh alpha volume automatically.

Old stacks may still leave behind a `nomadbase_pgdata` volume in Docker, but the current setup now boots against the new `nomadbase_pgdata_alpha` volume instead.

## First checks after deploy

Open:

- `/`
- `/api/health`
- `/api/docs`

The homepage should show a frontend shell and try to read API health through nginx.
The map tab should render alpha sample places right away after a healthy first boot.

## Known limitations

- The frontend is a thin first-deploy shell, not the full product UI yet.
- `trips`, `tracking`, and `admin` are still mostly placeholder endpoints.
- Local Docker runtime was not verifiable in this coding session because Docker Desktop was failing in the IDE environment.
