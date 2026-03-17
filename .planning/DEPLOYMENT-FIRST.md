# Deployment-First Path

## Intent

NomadBase should reach a first private deployment as early as possible so real travel usage can shape the product. The goal is not to finish the full roadmap before shipping. The goal is to deploy the smallest credible slice that proves the stack, data flow, and core travel value.

## Current Reality

- The repo already contains a backend scaffold: FastAPI app wiring, route groups, SQLAlchemy models, Docker Compose, and PostGIS.
- The repo does not yet contain a `frontend/` app, OSM import pipeline, Alembic revision, tests, or a repeatable deployment smoke check.
- Planning docs currently overstate Phase 1 progress on paper while understating the fact that backend implementation has already started.

## Recommended First Deployment

Ship a private `Map + Save` beta, not the full v1 roadmap.

The first deployment should include:

- PostgreSQL + PostGIS running in Docker Compose
- FastAPI with a real schema bootstrap path
- One real place dataset loaded into `places`
- Real endpoints for map listing and saved places
- A thin client surface for using those endpoints

The first deployment should explicitly defer:

- Full PWA polish
- Offline caching
- Cron-based imports
- Admin UI
- Trips beyond a minimal data model
- Expense and visit tracking

## Ordered Work

1. Make database bootstrap real.
   Create the first Alembic revision and ensure deployment runs `alembic upgrade head`.

2. Add one data-ingest path.
   The fastest option is a manual seed import for one small region or a checked-in seed dataset. Do not block on full automation yet.

3. Turn `GET /api/map/places` into a real endpoint.
   Add a PostGIS-backed query with a small, explicit filter set rather than designing the full discovery system up front.

4. Turn `/api/saves` into a real endpoint pair.
   Listing and creating saved places is enough for the first feedback loop.

5. Add the thinnest possible frontend surface.
   Prefer a simple Vue shell with one map/list screen over full PWA work. If needed, Swagger can be the temporary verification surface before the frontend lands.

6. Harden deployment defaults.
   Remove `--reload`, avoid bind-mounted source in the production path, and tighten config defaults so the homeserver deployment is reproducible.

7. Add a smoke check.
   Verify database availability, applied migrations, health response, and one real data endpoint from a fresh deployment.

## Exit Criteria

The first private deployment is good enough when all of the following are true:

- `docker compose up` can bring up the stack after Docker itself is healthy
- the database schema exists on a fresh environment
- at least one region or seed dataset produces non-empty `places`
- `GET /api/map/places` returns real data
- `GET /api/saves` and `POST /api/saves` persist data correctly
- there is at least one usable client surface to exercise the slice end to end

## Supporting Documents

- `.planning/codebase/STACK.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/CONCERNS.md`
- `.planning/codebase/TESTING.md`

## Notes

- Local Docker validation in this session was blocked by Docker Desktop returning `500 Internal Server Error` from the daemon API. Treat runtime verification as incomplete until that host issue is cleared.
- The roadmap remains useful as product direction, but near-term execution should follow this deployment-first sequence instead of waiting for full Phase 1 polish.
