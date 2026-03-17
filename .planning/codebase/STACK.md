# Technology Stack

**Analysis Date:** 2026-03-17

## Languages

**Primary:**
- Python 3.12+ - backend API, models, and migrations live in `backend/app/`, `backend/alembic/env.py`, and `backend/pyproject.toml`

**Secondary:**
- SQL / PostgreSQL-specific schema features - async PostgreSQL types (`UUID`, `JSONB`) and PostGIS geometry columns are used in `backend/app/models/place.py`, `backend/app/models/city.py`, and `backend/alembic/env.py`
- YAML / Dockerfile configuration - container orchestration and runtime packaging are defined in `docker-compose.yml` and `backend/Dockerfile`

## Runtime

**Environment:**
- CPython 3.12 via `python:3.12-slim` in `backend/Dockerfile`
- Container-first local runtime via Docker Compose in `docker-compose.yml`

**Package Manager:**
- `pip` via pinned dependencies in `backend/requirements.txt`
- Lockfile: missing

## Frameworks

**Core:**
- FastAPI 0.115.6 - API application and route mounting in `backend/app/main.py`
- SQLAlchemy asyncio 2.0.36 - async engine/session setup in `backend/app/db.py`
- GeoAlchemy2 0.15.2 - PostGIS `Geometry("POINT", srid=4326)` columns in `backend/app/models/place.py` and `backend/app/models/city.py`
- Pydantic Settings 2.7.1 - environment-backed settings in `backend/app/config.py`

**Testing:**
- Not detected - no `pytest`, `unittest`, `vitest`, `jest`, or test files were found under the repo

**Build/Dev:**
- Uvicorn[standard] 0.34.0 - ASGI server launched by `backend/Dockerfile`
- Alembic 1.14.0 - migration tooling configured in `backend/alembic.ini` and `backend/alembic/env.py`
- Docker Compose - local orchestration for the database and API in `docker-compose.yml`

## Key Dependencies

**Critical:**
- `fastapi==0.115.6` - HTTP API framework wired in `backend/app/main.py`
- `sqlalchemy[asyncio]==2.0.36` - ORM and async DB access in `backend/app/db.py`
- `asyncpg==0.30.0` - PostgreSQL async driver used by `DATABASE_URL` in `backend/app/config.py`
- `geoalchemy2==0.15.2` - spatial model support for PostGIS-backed geometry fields in `backend/app/models/place.py`
- `alembic==1.14.0` - schema migration entrypoint in `backend/alembic/env.py`

**Infrastructure:**
- `postgis/postgis:16-3.4` - PostgreSQL 16 + PostGIS 3.4 database runtime in `docker-compose.yml`
- `pydantic-settings==2.7.1` - settings loader for `.env`/environment variables in `backend/app/config.py`
- `httpx==0.28.1` - declared in `backend/requirements.txt`, but no current imports or outbound HTTP usage were found under `backend/app/` or `backend/alembic/`

## Configuration

**Environment:**
- `backend/app/config.py` loads settings from a `.env` file and environment variables using `BaseSettings`
- Implemented settings are `DATABASE_URL`, `APP_NAME`, `DEBUG`, and `API_V1_PREFIX` in `backend/app/config.py`
- `docker-compose.yml` injects `DATABASE_URL` into the `api` container and `DB_PASSWORD` into both `db` and `api`
- `.env.example` exists at repo root and `backend/.env.example`; contents were intentionally not inspected

**Build:**
- `docker-compose.yml` defines the current runnable stack
- `backend/Dockerfile` defines the API image
- `backend/alembic.ini` and `backend/alembic/env.py` define migration configuration
- `backend/pyproject.toml` defines Python package metadata and required Python version

## Platform Requirements

**Development:**
- Docker Engine + Docker Compose to run `db` and `api` from `docker-compose.yml`
- PostgreSQL/PostGIS is expected through the `postgis/postgis:16-3.4` container rather than a host install
- Python 3.12+ is required if running the backend outside containers, per `backend/pyproject.toml`

**Production:**
- The only implemented deployment artifact is a two-service Docker Compose stack (`db`, `api`) in `docker-compose.yml`
- Homeserver + VPN deployment is documented in `.planning/PROJECT.md` and `.planning/STATE.md`, but no provisioning, reverse proxy, or CI/CD config is implemented in-repo

## Implementation vs Planning Mismatches

- `.planning/PROJECT.md` and `.planning/phases/01-infrastructure/01-03-PLAN.md` define a target frontend stack of Vue 3, Vite, Pinia, Vue Router, and a PWA shell, but no `frontend/` directory, Node manifest, or frontend build config exists in the current repo
- `.planning/PROJECT.md` and `.planning/phases/01-infrastructure/01-02-PLAN.md` define an OSM import pipeline using Geofabrik extracts, `osmium`, CLI tooling, and cron scripts, but no `backend/app/osm/` package or `backend/scripts/` implementation exists
- `.planning/PROJECT.md` lists Wikipedia/Wikidata as enrichment sources, but no SDK/client, outbound HTTP calls, or ingestion code exists; `httpx` is present only as an unused dependency in `backend/requirements.txt`
- `.planning/ROADMAP.md` expects a full stack that includes an installable PWA; the implemented stack today is backend-only plus PostGIS infrastructure

---

*Stack analysis: 2026-03-17*
