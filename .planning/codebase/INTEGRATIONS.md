# External Integrations

**Analysis Date:** 2026-03-17

## APIs & External Services

**Infrastructure Services:**
- PostgreSQL + PostGIS - primary persistence and geospatial backing store for the API
  - SDK/Client: `sqlalchemy[asyncio]`, `asyncpg`, `geoalchemy2`
  - Auth: `DATABASE_URL` in `backend/app/config.py`; `DB_PASSWORD` in `docker-compose.yml`

**Outbound HTTP APIs:**
- Not detected - no implemented outbound HTTP clients, API SDK imports, or webhook senders were found in `backend/app/` or `backend/alembic/`

## Data Storage

**Databases:**
- PostgreSQL 16 + PostGIS 3.4 via `postgis/postgis:16-3.4` in `docker-compose.yml`
  - Connection: `DATABASE_URL`
  - Client: async SQLAlchemy engine/session in `backend/app/db.py`
  - Spatial usage: `Geometry("POINT", srid=4326)` columns and GiST indexing in `backend/app/models/place.py` and `backend/app/models/city.py`

**File Storage:**
- Local Docker-managed volume `pgdata` in `docker-compose.yml`
- No object storage or blob storage integration detected

**Caching:**
- None

## Authentication & Identity

**Auth Provider:**
- None
  - Implementation: FastAPI routes in `backend/app/main.py` and `backend/app/routers/*.py` are unauthenticated; `.planning/PROJECT.md` explicitly keeps multi-user auth out of the MVP

## Monitoring & Observability

**Error Tracking:**
- None detected

**Logs:**
- Container stdout/stderr from `uvicorn` launched in `backend/Dockerfile`
- Alembic logger configuration in `backend/alembic.ini`
- No application-level structured logging, metrics, or tracing integration detected in `backend/app/`

## CI/CD & Deployment

**Hosting:**
- Docker Compose deployment is the only implemented hosting path in `docker-compose.yml`
- `.planning/PROJECT.md` and `.planning/STATE.md` describe a homeserver reached over VPN, but that access layer is not represented by code or deployment manifests in the repo

**CI Pipeline:**
- None detected - no `.github/workflows/` or other CI configuration files were found

## Environment Configuration

**Required env vars:**
- `DATABASE_URL` - consumed by `backend/app/config.py` and `backend/alembic/env.py`
- `DB_PASSWORD` - consumed by `docker-compose.yml` to initialize PostgreSQL and compose the API connection string
- `APP_NAME` - optional app metadata override in `backend/app/config.py`
- `DEBUG` - optional SQLAlchemy/FastAPI runtime flag in `backend/app/config.py`
- `API_V1_PREFIX` - optional prefix setting in `backend/app/config.py`

**Secrets location:**
- Runtime secrets are expected from environment variables or untracked `.env` files referenced by `backend/app/config.py` and `docker-compose.yml`
- `.env.example` exists at repo root and `backend/.env.example`; contents were intentionally not inspected

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Implementation vs Planning Mismatches

- `.planning/PROJECT.md` and `.planning/phases/01-infrastructure/01-02-PLAN.md` expect OpenStreetMap / Geofabrik ingestion via `backend/app/osm/*.py` and shell scripts, but no import client, downloader, parser, or cron wrapper exists in the current implementation
- `.planning/PROJECT.md` names Wikipedia/Wikidata as data sources, but there is no enrichment pipeline, background job, or outbound API client in `backend/app/`
- `.planning/PROJECT.md` and `.planning/phases/01-infrastructure/01-03-PLAN.md` expect a frontend PWA and map stack (Vue 3, Vite, MapLibre GL JS), but there is no frontend codebase and therefore no implemented tile provider, browser auth flow, or client-to-API integration
- `backend/requirements.txt` includes `httpx==0.28.1`, but no live integration currently uses it

---

*Integration audit: 2026-03-17*
