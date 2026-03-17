# Architecture

**Analysis Date:** 2026-03-17

## Pattern Overview

**Overall:** Planning-led monorepo with a partially implemented backend-first service architecture.

**Key Characteristics:**
- Use `docker-compose.yml` as the top-level runtime orchestrator for infrastructure and application services.
- Treat `backend/app/main.py` as the composition root that wires all HTTP route groups into one FastAPI app.
- Keep domain persistence in `backend/app/models/*.py` and shared database access in `backend/app/db.py`; there is no service or repository layer yet.
- Read the planning system in `.planning/` as intended architecture, not deployed architecture; several planned layers are not present in the working tree.

## Layers

**Planning Layer:**
- Purpose: Define product scope, roadmap phases, and intended file layout before implementation.
- Location: `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/phases/01-infrastructure/*.md`, `nomadbase_project_foundation.md`, `nomadbase_data_model_and_system.md`
- Contains: Product intent, roadmap milestones, phase plans, target monorepo shape, and conceptual system design.
- Depends on: None inside the codebase.
- Used by: Humans and automation planning work; current code follows parts of `01-01-PLAN.md` but not the full Phase 1 scope.

**Runtime / Container Layer:**
- Purpose: Start the deployable stack and define container boundaries.
- Location: `docker-compose.yml`, `backend/Dockerfile`
- Contains: `db` and `api` services, database healthcheck, API build/runtime instructions.
- Depends on: `backend/requirements.txt`, `backend/app/main.py`, environment variables from `.env` or shell.
- Used by: Local/container execution of the backend and PostGIS database.

**API Composition Layer:**
- Purpose: Expose HTTP endpoints and group functionality by feature area.
- Location: `backend/app/main.py`, `backend/app/routers/health.py`, `backend/app/routers/map.py`, `backend/app/routers/saves.py`, `backend/app/routers/trips.py`, `backend/app/routers/tracking.py`, `backend/app/routers/admin.py`
- Contains: FastAPI app construction, CORS middleware, router registration, health endpoint, and stub responses for planned feature groups.
- Depends on: `backend/app/config.py`, `backend/app/db.py`, `backend/app/schemas/health.py`
- Used by: All external API consumers. There is no frontend consumer in the repository yet.

**Configuration / Schema Layer:**
- Purpose: Centralize runtime settings and Pydantic response models.
- Location: `backend/app/config.py`, `backend/app/schemas/health.py`
- Contains: `Settings` for `DATABASE_URL`, `APP_NAME`, `DEBUG`, `API_V1_PREFIX`, plus the `HealthResponse` schema.
- Depends on: Pydantic settings and environment configuration.
- Used by: `backend/app/main.py`, `backend/app/db.py`, `backend/app/routers/health.py`, `backend/alembic/env.py`

**Persistence Layer:**
- Purpose: Define the relational and geospatial data model and create DB sessions.
- Location: `backend/app/db.py`, `backend/app/models/base.py`, `backend/app/models/__init__.py`, `backend/app/models/place.py`, `backend/app/models/saved_place.py`, `backend/app/models/trip.py`, `backend/app/models/city.py`, `backend/app/models/expense.py`, `backend/app/models/visit.py`, `backend/app/models/preference.py`
- Contains: Async SQLAlchemy engine/session factory, `Base` metadata, timestamp mixin, domain tables, PostGIS geometry columns, and relationships.
- Depends on: `backend/app/config.py`, SQLAlchemy, GeoAlchemy2, PostgreSQL dialect types.
- Used by: `backend/app/db.py` today and `backend/alembic/env.py` for migration metadata loading. The routers do not query these models yet.

**Migration Layer:**
- Purpose: Bridge model metadata into Alembic migration execution.
- Location: `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/.gitkeep`
- Contains: Alembic config, async migration environment, explicit model imports for autogeneration.
- Depends on: `backend/app/models/__init__.py`, `backend/app/config.py`
- Used by: Manual Alembic commands. No concrete revision file exists under `backend/alembic/versions/`.

## Data Flow

**Health Check Request:**

1. Container runtime starts `uvicorn` from `backend/Dockerfile`, which loads `backend/app/main.py`.
2. FastAPI routes `/api/health` into `backend/app/routers/health.py`.
3. `health_check()` calls `check_db()` from `backend/app/db.py`.
4. `check_db()` opens an async session and runs `SELECT 1`.
5. `backend/app/schemas/health.py` shapes the HTTP response.

**Feature Stub Request:**

1. A request hits one of the registered prefixes in `backend/app/main.py`, such as `/api/map` or `/api/tracking`.
2. The matching router in `backend/app/routers/*.py` returns a placeholder payload immediately.
3. No model access, business logic, or persistence occurs.

**Schema / Migration Flow:**

1. Domain tables are declared in `backend/app/models/*.py`.
2. `backend/app/models/__init__.py` re-exports models so Alembic can load them centrally.
3. `backend/alembic/env.py` imports the model package and sets `target_metadata = Base.metadata`.
4. Revision generation is intended to happen through Alembic, but `backend/alembic/versions/` currently contains only `.gitkeep`.

**State Management:**
- Backend state is request-scoped and DB-backed through `async_session_maker` in `backend/app/db.py`.
- There is no application service state layer, background job layer, or frontend state store in the repository.

## Key Abstractions

**FastAPI Composition Root:**
- Purpose: Centralize app construction and route registration.
- Examples: `backend/app/main.py`
- Pattern: One module instantiates the app, adds middleware, and includes all routers explicitly.

**Router Modules:**
- Purpose: Group endpoints by feature area and keep route registration flat.
- Examples: `backend/app/routers/map.py`, `backend/app/routers/saves.py`, `backend/app/routers/tracking.py`
- Pattern: One `APIRouter` per feature file with lightweight handlers.

**Domain Models:**
- Purpose: Represent the core travel entities planned in the product documents.
- Examples: `backend/app/models/place.py`, `backend/app/models/trip.py`, `backend/app/models/expense.py`
- Pattern: SQLAlchemy declarative models with UUID primary keys, optional relationships, and PostGIS geometry where location matters.

**Shared Settings Object:**
- Purpose: Provide one importable configuration surface.
- Examples: `backend/app/config.py`
- Pattern: Instantiate `Settings()` at module load and import `settings` where needed.

**Migration Metadata Bootstrap:**
- Purpose: Keep Alembic aware of all model tables.
- Examples: `backend/alembic/env.py`, `backend/app/models/__init__.py`
- Pattern: Eagerly import each model in Alembic rather than relying on discovery.

## Entry Points

**Container Stack:**
- Location: `docker-compose.yml`
- Triggers: `docker compose up`
- Responsibilities: Start `db` and `api`, inject `DATABASE_URL`, and expose ports `5432` and `8000`.

**HTTP API App:**
- Location: `backend/app/main.py`
- Triggers: `uvicorn app.main:app`
- Responsibilities: Build the FastAPI app and register six route groups.

**Migration Runtime:**
- Location: `backend/alembic/env.py`
- Triggers: `alembic revision`, `alembic upgrade`, and other Alembic commands from `backend/`
- Responsibilities: Bind runtime config to Alembic and expose model metadata.

## Error Handling

**Strategy:** Minimal and localized.

**Patterns:**
- Use boolean degradation in `backend/app/db.py` and `backend/app/routers/health.py`: DB exceptions are swallowed and translated into `database: false`.
- Return placeholder 200 responses from `backend/app/routers/map.py`, `backend/app/routers/saves.py`, `backend/app/routers/trips.py`, `backend/app/routers/tracking.py`, and `backend/app/routers/admin.py` instead of raising not-implemented errors.
- No centralized exception handlers, typed domain errors, or validation error shaping beyond default FastAPI behavior.

## Cross-Cutting Concerns

**Logging:** Only Alembic logging is configured in `backend/alembic.ini`. The FastAPI app uses no explicit structured logging.
**Validation:** Response validation exists only for `/api/health` via `backend/app/schemas/health.py`. Other routes return untyped dictionaries.
**Authentication:** Not present. This matches the single-user MVP direction in `.planning/PROJECT.md`.

## Roadmap / Implementation Gaps

**Planned Monorepo vs Current Tree:**
- `.planning/phases/01-infrastructure/01-CONTEXT.md` and `.planning/phases/01-infrastructure/01-03-PLAN.md` define a `/backend` + `/frontend` monorepo.
- The working tree contains `backend/` but no `frontend/` directory, so the PWA shell, router, service worker, and bottom-nav app shell are absent.

**Planned Import Pipeline vs Current Tree:**
- `.planning/phases/01-infrastructure/01-02-PLAN.md` expects importer modules and scripts such as `backend/app/osm/*` and `backend/scripts/osm_cronjob.sh`.
- No importer package, script directory, download workflow, or cron wrapper exists under `backend/`.

**Model Metadata vs Executable Schema:**
- `backend/app/models/*.py` and `backend/alembic/env.py` establish metadata for an initial schema.
- `backend/alembic/versions/` has no revision files, so the schema described by the models is not materialized as a tracked migration history.

**Roadmap Status vs Working Tree State:**
- `.planning/ROADMAP.md` and `.planning/STATE.md` still report Phase 1 as planning-only with `0/3` plans complete.
- The working tree already contains part of `01-01-PLAN.md` in `backend/app/main.py` and `backend/app/routers/*.py`, so implementation has started without the planning status reflecting it.

**Target Deployment vs Actual Deployment Surface:**
- `.planning/ROADMAP.md` success criteria for Phase 1 require a full stack with an installable app shell.
- `docker-compose.yml` currently starts only `db` and `api`; there is no frontend service, reverse proxy, or static asset delivery path.

---

*Architecture analysis: 2026-03-17*
