# Phase 1: Infrastructure - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Deploy the foundational skeleton: Docker Compose stack running FastAPI + PostgreSQL/PostGIS, REST API with stub routes for all feature areas, OSM data import pipeline via Geofabrik extracts, and a PWA shell installable on mobile with bottom navigation.

</domain>

<decisions>
## Implementation Decisions

### Project Structure
- Monorepo: single repository with /backend and /frontend folders
- Docker Compose orchestrates everything — development happens on homeserver only (no local dev setup)
- Homeserver accessed via VPN (Tailscale/WireGuard)

### Navigation & App Shell
- 4 bottom tabs: Map, Saved, Trips, More
- "More" tab contains: Track (expenses/visits), Settings, and future features
- Map is the default/home screen when opening the app

### Visual Design
- Modern, clean design with both Light and Dark mode support
- User can switch between light/dark (system preference as default)
- Color palette and tones at Claude's discretion — aim for modern mobile-first feel

### Claude's Discretion
- Frontend framework choice (Vue/Vite/Pinia from foundation doc, or alternatives if better suited)
- TypeScript vs JavaScript
- CSS framework (Tailwind, plain CSS, etc.)
- Backend folder structure and code organization
- Python dependency management
- OSM import CLI tool design and first test region
- Database schema details and PostGIS indexing strategy
- Service worker implementation approach
- API versioning and error handling patterns
- All technical architecture and implementation patterns

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Vision & Data Model
- `nomadbase_project_foundation.md` — Product vision, app modes, navigation structure, technical architecture overview, MVP scope
- `nomadbase_data_model_and_system.md` — Core entities (Trip, City, Place, SavedPlace, Visit, Expense), data relationships, geospatial requirements, API concepts, offline strategy

### Planning
- `.planning/REQUIREMENTS.md` — v1 requirements with IDs (INFR-01 through INFR-04 for this phase)
- `.planning/ROADMAP.md` — Phase goals and success criteria

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project, no code exists yet

### Established Patterns
- None — this phase establishes all patterns

### Integration Points
- Docker Compose is the single entry point for the entire stack
- FastAPI serves both the REST API and the PWA static files (or separate frontend container)

</code_context>

<specifics>
## Specific Ideas

- App must be usable within 1-2 months before a 4-month trip through Europe and Canada — tight timeline, prioritize getting something deployed fast
- 100k+ POI data volume requires PostGIS spatial indexes to be correct from Phase 1
- Pre-ingest OSM data via Geofabrik extracts before trip departure (not live Overpass API)
- MapLibre GL JS chosen over Leaflet for WebGL performance
- No Redis in MVP — single-user traffic doesn't justify it
- Single currency EUR for expenses
- User wants deployable base as fast as possible

</specifics>

<deferred>
## Deferred Ideas

- Theme customization UI (let user pick color tones) — future settings feature
- Offline map tile caching — v2 requirement (MAP-05)
- Multi-currency support — v2 requirement (ADVN-05)

</deferred>

---

*Phase: 01-infrastructure*
*Context gathered: 2026-03-17*
