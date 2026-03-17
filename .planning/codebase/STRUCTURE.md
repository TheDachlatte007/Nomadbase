# Codebase Structure

**Analysis Date:** 2026-03-17

## Directory Layout

```text
[project-root]/
├── .planning/                    # Project planning system, roadmap, state, and phase plans
│   ├── codebase/                 # Generated codebase map documents
│   └── phases/01-infrastructure/ # Phase 1 context and plan documents
├── backend/                      # Python API service, models, and Alembic config
│   ├── alembic/                  # Alembic environment and revision directory
│   └── app/                      # FastAPI application package
├── docker-compose.yml            # Top-level container orchestration
├── nomadbase_data_model_and_system.md # Conceptual system/data model reference
└── nomadbase_project_foundation.md    # Product and technical foundation reference
```

## Directory Purposes

**`.planning/`:**
- Purpose: Hold the project-management source of truth.
- Contains: `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, phase context/plan files, and generated mapping docs.
- Key files: `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`

**`.planning/phases/01-infrastructure/`:**
- Purpose: Capture the intended implementation shape for Phase 1.
- Contains: `01-CONTEXT.md`, `01-01-PLAN.md`, `01-02-PLAN.md`, `01-03-PLAN.md`
- Key files: `.planning/phases/01-infrastructure/01-01-PLAN.md`, `.planning/phases/01-infrastructure/01-02-PLAN.md`, `.planning/phases/01-infrastructure/01-03-PLAN.md`

**`backend/`:**
- Purpose: House the only implemented application code in the repository.
- Contains: Python packaging/config files, Dockerfile, Alembic config, the `app/` package, and `.env.example`.
- Key files: `backend/pyproject.toml`, `backend/requirements.txt`, `backend/Dockerfile`, `backend/alembic.ini`

**`backend/app/`:**
- Purpose: Hold runtime application modules for the API service.
- Contains: `main.py`, `config.py`, `db.py`, plus `models/`, `routers/`, and `schemas/`.
- Key files: `backend/app/main.py`, `backend/app/config.py`, `backend/app/db.py`

**`backend/app/models/`:**
- Purpose: Define persistent domain entities.
- Contains: Declarative model files for `Place`, `SavedPlace`, `Trip`, `City`, `Expense`, `Visit`, and `UserPreference`.
- Key files: `backend/app/models/place.py`, `backend/app/models/trip.py`, `backend/app/models/expense.py`, `backend/app/models/__init__.py`

**`backend/app/routers/`:**
- Purpose: Split the HTTP API by feature area.
- Contains: `health.py`, `map.py`, `saves.py`, `trips.py`, `tracking.py`, `admin.py`, and `__init__.py`.
- Key files: `backend/app/routers/health.py`, `backend/app/routers/map.py`, `backend/app/routers/admin.py`

**`backend/app/schemas/`:**
- Purpose: Hold request/response models.
- Contains: Only the health response schema today.
- Key files: `backend/app/schemas/health.py`

**`backend/alembic/`:**
- Purpose: Configure migrations for the backend schema.
- Contains: `env.py` and `versions/`.
- Key files: `backend/alembic/env.py`, `backend/alembic/versions/.gitkeep`

## Key File Locations

**Entry Points:**
- `docker-compose.yml`: Starts the `db` and `api` services.
- `backend/app/main.py`: FastAPI application entry point.
- `backend/alembic/env.py`: Alembic runtime entry point for migrations.

**Configuration:**
- `backend/pyproject.toml`: Python project metadata and Alembic script location.
- `backend/requirements.txt`: Runtime dependencies.
- `backend/alembic.ini`: Alembic logging and config bootstrap.
- `backend/app/config.py`: Runtime settings from environment.
- `backend/.env.example`: Backend environment example file.
- `.env.example`: Root-level environment example file.

**Core Logic:**
- `backend/app/db.py`: Async engine/session creation and DB connectivity check.
- `backend/app/models/place.py`: Largest domain model and primary geospatial table.
- `backend/app/models/trip.py`: Trip aggregate root for travel planning.
- `backend/app/models/city.py`: Trip child entity with optional point geometry.
- `backend/app/routers/*.py`: HTTP surface grouped by feature domain.

**Testing:**
- Not detected. There are no test directories, test files, or test configuration files in the repository root or `backend/`.

## Naming Conventions

**Files:**
- Use lowercase snake_case for Python modules such as `backend/app/db.py` and `backend/app/models/saved_place.py`.
- Name router modules by feature area, mostly plural nouns: `backend/app/routers/saves.py`, `backend/app/routers/trips.py`, `backend/app/routers/tracking.py`.
- Keep planning files in numbered, uppercase-suffix form such as `.planning/phases/01-infrastructure/01-01-PLAN.md`.

**Directories:**
- Use lowercase names for runtime code directories such as `backend/`, `backend/app/`, `backend/app/models/`, and `backend/app/routers/`.
- Use descriptive, phase-oriented names under `.planning/phases/`, such as `.planning/phases/01-infrastructure/`.

## Where to Add New Code

**New Feature:**
- Primary API endpoints: `backend/app/routers/`
- Persistence models: `backend/app/models/`
- Shared request/response schemas: `backend/app/schemas/`
- Tests: Create a new `backend/tests/` package; no existing test directory is established.

**New Component/Module:**
- Backend runtime module: `backend/app/`
- Migration support for new tables/columns: add a revision under `backend/alembic/versions/`

**Utilities:**
- Shared backend helpers: `backend/app/`
- Import or automation tooling: the plans point to `backend/app/osm/` and `backend/scripts/`, but neither directory exists yet; create them only when implementing the importer scope from `.planning/phases/01-infrastructure/01-02-PLAN.md`.

## Special Directories

**`.planning/codebase/`:**
- Purpose: Generated reference documents for future planning and execution.
- Generated: Yes
- Committed: Not yet in the current tree snapshot

**`backend/alembic/versions/`:**
- Purpose: Store migration revision files.
- Generated: Yes
- Committed: Yes, but only `.gitkeep` exists

**`backend/app/__pycache__/`:**
- Purpose: Python bytecode cache for the app package.
- Generated: Yes
- Committed: No

**`backend/app/models/__pycache__/`:**
- Purpose: Python bytecode cache for model modules.
- Generated: Yes
- Committed: No

## Planning / Implementation Gaps

**Missing Frontend Tree:**
- The planned structure in `.planning/phases/01-infrastructure/01-CONTEXT.md` and `.planning/phases/01-infrastructure/01-03-PLAN.md` expects `frontend/` with `src/`, `public/`, and PWA assets.
- No `frontend/` directory exists, so the repository is backend-only despite the roadmap describing a full PWA monorepo.

**Missing Importer Directories:**
- `.planning/phases/01-infrastructure/01-02-PLAN.md` expects importer code under paths such as `backend/app/osm/` and scripts under `backend/scripts/`.
- Those directories do not exist, so there is no place in the current tree for the planned OSM CLI and cronjob automation.

**Migration Directory Not Populated:**
- `backend/alembic/versions/` exists only as a placeholder.
- The structure for tracked schema evolution is present, but the initial migration file planned in `.planning/phases/01-infrastructure/01-01-PLAN.md` is missing.

**Testing Structure Missing Entirely:**
- The plans imply verification steps, but there is no `backend/tests/`, `tests/`, `pytest.ini`, or similar test harness in the repository.
- New implementation work will need to establish a testing location before test coverage can accumulate.

**Plan Status Lags Working Tree:**
- `.planning/ROADMAP.md` and `.planning/STATE.md` still describe Phase 1 as not started from an execution perspective.
- The working tree already contains `backend/app/main.py` and `backend/app/routers/*.py`, so the code structure is ahead of the recorded roadmap status.

---

*Structure analysis: 2026-03-17*
