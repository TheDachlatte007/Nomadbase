# Deploy Notes

## Current target

This repository is prepared for a first private deployment through GitHub and Portainer.

## Services

- `db`: PostgreSQL 16 with PostGIS 3.4
- `api`: FastAPI backend on port `8000`
- `frontend`: static web shell with nginx proxy on port `80`

## Required environment

- `DB_PASSWORD`

Example:

```env
DB_PASSWORD=change_me
```

## Expected first-run behavior

The API container runs:

1. `alembic upgrade head`
2. `python -m app.seed_alpha` when `SEED_ALPHA_DATA=true`
3. `uvicorn app.main:app --host 0.0.0.0 --port 8000`

That means the database schema should be created automatically on first deploy once the database is reachable.

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
