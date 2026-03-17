# Coding Conventions

**Analysis Date:** 2026-03-17

## Naming Patterns

**Files:**
- Use `snake_case.py` for Python modules. Current examples: `backend/app/config.py`, `backend/app/db.py`, `backend/app/routers/health.py`, `backend/app/models/saved_place.py`.

**Functions:**
- Use `snake_case` for functions and route handlers. Current examples: `health_check` in `backend/app/routers/health.py`, `list_trips` in `backend/app/routers/trips.py`, `check_db` in `backend/app/db.py`.
- Use `async def` for FastAPI route handlers and async database helpers. Current examples: every handler in `backend/app/routers/*.py` and both functions in `backend/app/db.py`.

**Variables:**
- Use `UPPER_SNAKE_CASE` for settings fields intended to map to environment variables in `backend/app/config.py` (`DATABASE_URL`, `APP_NAME`, `DEBUG`, `API_V1_PREFIX`).
- Use `snake_case` for module-level instances and model fields. Current examples: `settings` in `backend/app/config.py`, `async_session_maker` in `backend/app/db.py`, `place_type` and `raw_osm_tags` in `backend/app/models/place.py`.

**Types:**
- Use `PascalCase` for Pydantic and SQLAlchemy classes. Current examples: `Settings` in `backend/app/config.py`, `HealthResponse` in `backend/app/schemas/health.py`, `Place` and `UserPreference` in `backend/app/models/*.py`.
- Use suffix-style names for mixins and response models. Current examples: `TimestampMixin` in `backend/app/models/base.py` and `HealthResponse` in `backend/app/schemas/health.py`.

## Code Style

**Formatting:**
- No formatter configuration is detected. `backend/pyproject.toml` contains only project metadata and Alembic script location.
- Follow the current style until a formatter is added:
  - 4-space indentation
  - one import per line
  - blank line between import blocks, declarations, and functions
  - short modules with a single responsibility
- Keep model field declarations vertically aligned as in `backend/app/models/place.py` and `backend/app/models/trip.py`.

**Linting:**
- No lint configuration is detected. There is no `ruff`, `black`, `flake8`, `mypy`, `pylint`, or `pre-commit` config in the repo root or `backend/`.
- `backend/alembic/env.py` uses `# noqa: F401`, which implies lint suppression is expected in at least one file, but no lint runner is configured to enforce or validate it.
- First deployment is slowed by the lack of baseline automation for import cleanup, dead-code detection, type checking, and unsafe exception handling.

## Import Organization

**Order:**
1. Standard library imports. Examples: `from uuid import uuid4` in `backend/app/models/*.py`, `import asyncio` in `backend/alembic/env.py`.
2. Third-party imports. Examples: `from fastapi import APIRouter` in `backend/app/routers/*.py`, `from sqlalchemy import Column` in `backend/app/models/*.py`.
3. Local `app.` imports. Examples: `from app.config import settings` in `backend/app/main.py` and `backend/app/db.py`, `from app.models.base import Base, TimestampMixin` in model modules.

**Path Aliases:**
- Use the `app.` package root for internal imports inside `backend/`. Current examples: `app.routers`, `app.models`, `app.schemas`.
- Do not introduce relative imports unless the package layout changes; the current codebase consistently prefers absolute package imports.

## Error Handling

**Patterns:**
- Database health handling is defensive but very coarse: `backend/app/db.py` catches `Exception` and converts every failure into `False`.
- Route handlers currently return plain dictionaries or a Pydantic response model and do not raise `HTTPException`. Current examples: `backend/app/routers/trips.py`, `backend/app/routers/map.py`, `backend/app/routers/admin.py`.
- No shared exception middleware, no domain exceptions, and no error logging are present in `backend/app/main.py` or `backend/app/routers/`.
- Use explicit FastAPI exceptions once real endpoints exist; the current placeholder-return pattern is only acceptable for stub routes.

## Logging

**Framework:** None detected in application code

**Patterns:**
- Application modules under `backend/app/` do not import `logging` and do not emit structured logs.
- Alembic logging is configured in `backend/alembic.ini` for migration runtime output only.
- First deployment is slowed by the absence of request logs, startup logs, and error logs in `backend/app/main.py` and `backend/app/db.py`.

## Comments

**When to Comment:**
- Comments are sparse and used only when a line needs context. Examples:
  - `# tighten in production` in `backend/app/main.py`
  - `# "ok" or "error"` in `backend/app/schemas/health.py`
  - status value hint in `backend/app/models/saved_place.py`
- Prefer concise comments that capture business constraints or deployment caveats. The existing code does not use explanatory block comments.

**JSDoc/TSDoc:**
- Not applicable. The current codebase is Python-only.
- Python docstrings are not used in `backend/app/`, `backend/alembic/`, or `backend/app/models/`.

## Function Design

**Size:** Keep functions small and single-purpose. Current handlers in `backend/app/routers/*.py` stay between one and a few return statements, and `backend/app/db.py` isolates session creation from health checking.

**Parameters:**
- Current route handlers generally take no parameters because most endpoints are placeholders.
- Dependency injection is prepared through `get_db` in `backend/app/db.py`, but no router currently consumes it.

**Return Values:**
- Health uses a typed Pydantic response model in `backend/app/routers/health.py`.
- Placeholder routers return ad hoc dictionaries with `data` and/or `message` keys in `backend/app/routers/map.py`, `backend/app/routers/saves.py`, `backend/app/routers/trips.py`, `backend/app/routers/tracking.py`, and `backend/app/routers/admin.py`.
- Standardize on Pydantic request/response schemas before implementing real write paths; current return shapes are inconsistent (`data: []`, `data: {}`, and message-only responses all exist).

## Module Design

**Exports:**
- Most modules rely on direct imports and do not define explicit exports.
- `backend/app/models/__init__.py` is the exception: it centralizes model imports and defines `__all__` for Alembic discovery.

**Barrel Files:**
- Use a barrel file only where the framework benefits from central registration. Current example: `backend/app/models/__init__.py`.
- `backend/app/routers/__init__.py` and `backend/app/schemas/__init__.py` are empty. Route registration is done from explicit imports in `backend/app/main.py`.

## Missing Standards

- No repository `.gitignore` is detected at project root, which makes accidental commit of generated files more likely. Current generated directories already exist under `backend/app/__pycache__` and `backend/app/models/__pycache__`.
- No formatter, linter, type checker, or pre-commit hooks are configured in `backend/pyproject.toml` or repo root.
- No service layer or repository layer exists between `backend/app/routers/` and the database utilities in `backend/app/db.py`, so handler conventions for validation, persistence, and error mapping are not yet defined.
- No API schema convention exists beyond `HealthResponse` in `backend/app/schemas/health.py`.

## Deployment Friction

- `backend/Dockerfile` starts `uvicorn` with `--reload`, which is a development convention, not a production one.
- `backend/app/main.py` allows `allow_origins=["*"]`, documented inline as temporary. This is an open deployment hardening task.
- Most routes are placeholders returning `"not yet implemented"` messages from `backend/app/routers/*.py`, so the API surface is not behaviorally stable enough for a first release.

---

*Convention analysis: 2026-03-17*
