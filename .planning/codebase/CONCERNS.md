# Codebase Concerns

**Analysis Date:** 2026-03-17

## Tech Debt

**Missing deployable user interface:**
- Issue: The repository has no `frontend/` tree even though `.planning/ROADMAP.md`, `.planning/PROJECT.md`, and `.planning/phases/01-infrastructure/01-03-PLAN.md` define an installable Vue/Vite PWA as part of Phase 1. `docker-compose.yml` only runs `db` and `api`.
- Files: `docker-compose.yml`, `.planning/ROADMAP.md`, `.planning/PROJECT.md`, `.planning/phases/01-infrastructure/01-03-PLAN.md`
- Impact: A first deployment cannot satisfy the project goal of "opens in a mobile browser as an installable PWA". The only reachable surface is the FastAPI API and docs from `backend/app/main.py`.
- Fix approach: Build the smallest possible `frontend/` shell first, add a `frontend` service to `docker-compose.yml`, and postpone non-essential polish. For first deployment, placeholder views are sufficient if the shell is installable and can call `/api/health`.

**No OSM import pipeline or seeded data path:**
- Issue: The repo contains models and stub routers, but no `backend/app/osm/` package, no `backend/scripts/import_osm.sh`, and no `backend/scripts/osm_cronjob.sh`. The POI ingestion path exists only in `.planning/phases/01-infrastructure/01-02-PLAN.md`.
- Files: `backend/app/models/place.py`, `backend/app/routers/map.py`, `.planning/REQUIREMENTS.md`, `.planning/phases/01-infrastructure/01-02-PLAN.md`
- Impact: The map experience cannot become useful because there is no way to load Geofabrik extracts into `places`. Shipping UI work before this lands produces an empty app.
- Fix approach: Implement a narrow import slice before broader feature work: CLI importer, one small pilot region, `./data:/app/data` volume, and a manual command path. Defer cron and admin triggers until after the first successful import.

**Schema bootstrap is not automated:**
- Issue: `backend/alembic/env.py` is configured, but `backend/alembic/versions/` contains only `.gitkeep`. `docker-compose.yml` has no migration step, init container, or startup hook, and `backend/app/main.py` does not create tables.
- Files: `backend/alembic/env.py`, `backend/alembic/versions/.gitkeep`, `docker-compose.yml`, `backend/app/main.py`
- Impact: A fresh deployment on an empty volume does not have a guaranteed schema, PostGIS indexes, or extension-validated tables. Future real endpoints will fail unless an operator performs manual Alembic work outside the checked-in flow.
- Fix approach: Generate and commit the initial Alembic revision, then make deployment run `alembic upgrade head` automatically. Keep "manual revision creation" out of first-deploy instructions.

**Production and development concerns are mixed together:**
- Issue: `backend/Dockerfile` runs `uvicorn` with `--reload`, and `docker-compose.yml` bind-mounts `./backend:/app`. That is convenient for local iteration but fragile for a homeserver deployment.
- Files: `backend/Dockerfile`, `docker-compose.yml`
- Impact: The default deploy path is a mutable dev container, not a reproducible production image. First deployment can drift with local file changes and has a higher chance of restart loops or inconsistent behavior.
- Fix approach: Keep the current compose file for development if needed, but add a production-oriented service definition or compose override that removes bind mounts and `--reload`.

## Known Bugs

**`docker compose up` cannot produce the planned mobile app entrypoint:**
- Symptoms: Starting the checked-in stack exposes PostgreSQL on `5432` and FastAPI on `8000`, but there is no service serving a user-facing app on port `80` or a PWA manifest.
- Files: `docker-compose.yml`, `backend/app/main.py`, `.planning/ROADMAP.md`
- Trigger: Run `docker compose up` on the current repo.
- Workaround: Use `http://<host>:8000/api/docs` or `/api/health` for backend verification only. There is no user workaround for the missing app shell.

**Fresh databases have no checked-in migration history:**
- Symptoms: `backend/alembic/env.py` can discover metadata, but the repository does not include an actual migration file in `backend/alembic/versions/`.
- Files: `backend/alembic/env.py`, `backend/alembic/versions/.gitkeep`, `backend/app/models/place.py`, `backend/app/models/trip.py`
- Trigger: Deploy against a new `pgdata` volume or any clean Postgres instance.
- Workaround: Create and apply a manual revision from inside the API environment, then keep that revision checked in going forward.

## Security Considerations

**Development defaults are deployable as-is:**
- Risk: `docker-compose.yml` publishes the database port publicly, `.env.example` and `backend/app/config.py` embed the dev password shape directly, and `backend/app/main.py` enables `allow_origins=["*"]` together with credentials.
- Files: `.env.example`, `backend/.env.example`, `backend/app/config.py`, `backend/app/main.py`, `docker-compose.yml`
- Current mitigation: `.planning/PROJECT.md` says the app runs behind VPN access, but that protection is not enforced anywhere in the repository.
- Recommendations: Remove the code-level default database URL, tighten CORS to trusted origins, avoid publishing `5432` unless a real external client needs it, and treat VPN exposure as defense in depth rather than the only control.

## Performance Bottlenecks

**The geospatial path is designed but not proven end-to-end:**
- Problem: `backend/app/models/place.py` defines `Geometry("POINT", srid=4326)` and GIST indexing, but there is no committed migration, no imported dataset, and `backend/app/routers/map.py` has no real bounding-box or nearby query implementation.
- Files: `backend/app/models/place.py`, `backend/app/routers/map.py`, `backend/alembic/versions/.gitkeep`, `.planning/PROJECT.md`
- Cause: Spatial performance work exists only at the schema-definition level; the operational path from import to indexed query to mobile rendering is still absent.
- Improvement path: Prove one thin vertical slice: apply migration, import one small region, add a single viewport query, and record explain/row-count results before importing Europe and Canada.

## Fragile Areas

**Phase 1 success criteria depend on files that do not exist yet:**
- Files: `.planning/ROADMAP.md`, `.planning/phases/01-infrastructure/01-02-PLAN.md`, `.planning/phases/01-infrastructure/01-03-PLAN.md`, `docker-compose.yml`
- Why fragile: The roadmap says Phase 1 should already produce a deployable skeleton, but the repo currently stops at backend stubs. Any plan that assumes the PWA shell or import pipeline exists will overestimate current readiness.
- Safe modification: Treat `backend/app/*` as only the first third of Phase 1. Do not begin Phase 2 map feature work until frontend, migrations, and one successful import are in place.
- Test coverage: No automated checks validate this dependency chain.

**The API layer is mostly placeholders backed by unproven persistence:**
- Files: `backend/app/routers/map.py`, `backend/app/routers/saves.py`, `backend/app/routers/trips.py`, `backend/app/routers/tracking.py`, `backend/app/routers/admin.py`
- Why fragile: Route groups exist, but every feature endpoint except health returns placeholder JSON. As soon as real CRUD work starts, missing migrations, missing data, and missing serialization patterns will surface together.
- Safe modification: Implement one feature vertically instead of broad stub replacement. Start with health + schema + import + one map read endpoint before saves/trips/tracking/admin.
- Test coverage: No API tests, schema tests, or compose smoke tests are present.

## Scaling Limits

**Current deployable scope is backend-only scaffolding:**
- Current capacity: One FastAPI process with stub routers and a Postgres service definition. No frontend container, no seed data, no automation for imports, and no committed migrations.
- Limit: The current repo cannot reach the first planned user milestone, let alone the stated Europe + Canada dataset size.
- Scaling path: First make a thin usable deployment work. After that, expand import coverage region by region and only then optimize for the full 100k+ POI target.

## Dependencies at Risk

**`postgis/postgis:16-3.4`:**
- Risk: The entire product depends on PostGIS being reachable and initialized correctly, but the repository has no fallback mode and no deployment-time verification script beyond planning text.
- Impact: If PostGIS bootstrapping or image pulls fail, every downstream feature is blocked because `Place.location` and `City.location` depend on it.
- Migration plan: Keep PostGIS, but add a checked-in smoke command that proves `PostGIS_Version()` and `alembic upgrade head` on the target homeserver before any frontend rollout.

## Missing Critical Features

**Installable PWA shell:**
- Problem: The MVP contract in `.planning/PROJECT.md` and `.planning/ROADMAP.md` requires a mobile-first PWA, but there is no `frontend/` implementation.
- Blocks: User-facing deployment, mobile validation, install prompt checks, and any real trip usage.

**POI ingestion and region seeding:**
- Problem: The product promise depends on pre-ingested OSM data, but there is no importer code or region data workflow in the repository.
- Blocks: Map discovery, save flow usefulness, and real-world testing before travel.

**Repeatable deployment automation:**
- Problem: There is no checked-in script or compose workflow that applies migrations, seeds data, and verifies the stack after boot.
- Blocks: Reliable first deployment and fast iteration on the homeserver.

## Test Coverage Gaps

**Deployment smoke path is untested:**
- What's not tested: `docker-compose.yml` startup, `backend/Dockerfile` image build, `backend/app/main.py` route registration, and schema bootstrap on a clean database.
- Files: `docker-compose.yml`, `backend/Dockerfile`, `backend/app/main.py`, `backend/alembic/env.py`
- Risk: The first deployment failure will happen during manual bring-up rather than in a repeatable check.
- Priority: High

**Persistence layer is untested:**
- What's not tested: Model metadata validity, Alembic autogeneration, PostGIS column creation, and foreign-key integrity across `Place`, `Trip`, `City`, `Expense`, `Visit`, and `SavedPlace`.
- Files: `backend/app/models/place.py`, `backend/app/models/saved_place.py`, `backend/app/models/trip.py`, `backend/app/models/city.py`, `backend/app/models/expense.py`, `backend/app/models/visit.py`
- Risk: Runtime schema failures will arrive late, when feature endpoints begin touching the database.
- Priority: High

**No vertical-slice verification for the map workflow:**
- What's not tested: Importing a region, reading POIs back through `/api/map/*`, and rendering those results in a browser-accessible UI.
- Files: `backend/app/routers/map.py`, `.planning/phases/01-infrastructure/01-02-PLAN.md`, `.planning/phases/01-infrastructure/01-03-PLAN.md`
- Risk: The highest-value user flow remains speculative even though it is the core product loop.
- Priority: High

## First Deployment Sequence

1. Commit the initial Alembic migration and make deployment run `alembic upgrade head` automatically.
2. Add the smallest `frontend/` PWA shell and wire it into `docker-compose.yml` so the app has a real mobile entrypoint.
3. Implement the narrow OSM importer path from `.planning/phases/01-infrastructure/01-02-PLAN.md`, but only prove one small region first.
4. Add a smoke script that checks `/api/health`, `PostGIS_Version()`, one imported row count, and the frontend index route.
5. Only after those four steps, start Phase 2 map/save feature work. Do not spend early time on cron, admin UI, or multi-region imports before the thin slice works.

---

*Concerns audit: 2026-03-17*
