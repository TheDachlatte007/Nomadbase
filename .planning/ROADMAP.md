# Roadmap: NomadBase

## Overview

NomadBase is built in five phases that follow the natural dependency chain: infrastructure first to establish the foundation, then the map and save features that form the core discovery loop, then trip planning that builds on saved places, then expense and visit tracking that closes the travel logging loop, and finally the admin panel that ties together data management and user preferences. The result is a fully functional personal travel operating system ready for a 4-month journey through Europe and Canada.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Infrastructure** - Docker Compose stack, PostGIS database, FastAPI REST API skeleton, and PWA foundation
- [ ] **Phase 2: Map + Save** - Interactive MapLibre map with POI filters and bookmarking with status tracking
- [ ] **Phase 3: Trips** - Trip creation with cities, place assignment, and map + list view
- [ ] **Phase 4: Tracking** - Expense recording in EUR and visit logging with overview summaries
- [ ] **Phase 5: Admin** - OSM data import management, system status, and user preferences

## Phase Details

### Phase 1: Infrastructure
**Goal**: The deployable skeleton is running — API serves requests, database accepts geodata, the app opens in a mobile browser as an installable PWA
**Depends on**: Nothing (first phase)
**Requirements**: INFR-01, INFR-02, INFR-03, INFR-04
**Success Criteria** (what must be TRUE):
  1. `docker compose up` starts the full stack (FastAPI + PostgreSQL/PostGIS) with no manual steps
  2. FastAPI health endpoint returns 200 and the database is reachable from the API container
  3. PostGIS extension is active and a sample OSM extract can be imported via the CLI pipeline
  4. Opening the app URL on mobile shows the PWA shell with a browser install prompt available
  5. All planned API route groups (map, saves, trips, tracking, admin) return 404 or stub responses — no 500s
**Plans:** 3 plans

Plans:
- [ ] 01-01-PLAN.md — Docker Compose + PostGIS database + FastAPI skeleton with stub routes (INFR-01, INFR-03)
- [ ] 01-02-PLAN.md — OSM data import pipeline: PBF parser, tag mapper, CLI tool, shell scripts (INFR-02)
- [ ] 01-03-PLAN.md — PWA frontend shell: Vue 3 + Vite, bottom nav, light/dark mode, service worker (INFR-04)

Current reality note:
The repository already contains a partial backend scaffold for 01-01, but there is still no `frontend/` tree, no real migration revision, and no import pipeline. Near-term execution should follow `.planning/DEPLOYMENT-FIRST.md` to get to the first deployable slice quickly.

### Phase 2: Map + Save
**Goal**: Users can explore POIs on a live map, filter by type and lifestyle, and bookmark places with personal status and notes
**Depends on**: Phase 1
**Requirements**: MAP-01, MAP-02, MAP-03, SAVE-01, SAVE-02
**Success Criteria** (what must be TRUE):
  1. The map loads with POI markers visible in the current viewport from the PostGIS database
  2. User can toggle type filters (restaurants, attractions, parks, cafes, hiking, viewpoints, cultural) and markers update without page reload
  3. User can toggle lifestyle filters (vegan, cheap, nature, hidden gems) and markers update without page reload
  4. User can tap a POI and save it with one of three statuses: Want to Visit, Visited, or Favorite
  5. User can open a saved place and add or edit personal notes
**Plans**: TBD

Current reality note:
The repo now contains a working alpha data flow for `places` and `saves`, including seeded sample places, stronger server-side ranking for intent queries, and note/status persistence. The missing pieces are the eventual MapLibre surface and deeper enrichment/import depth.

### Phase 3: Trips
**Goal**: Users can organize their journey into named trips with cities and planned places, viewable as both a map and a list
**Depends on**: Phase 2
**Requirements**: TRIP-01, TRIP-02, TRIP-03, TRIP-04
**Success Criteria** (what must be TRUE):
  1. User can create a trip with a name, start date, end date, and notes
  2. User can add one or more cities to a trip
  3. User can add a saved place to a city within a trip
  4. User can view a trip as a map showing pins for all assigned places alongside a scrollable side list
**Plans**: TBD

Current reality note:
Trip creation, ordered city routes, participant management, city-assigned trip saves, and a first trip map/list planner are now live in alpha form. The biggest open pieces are richer city-level summaries, smarter assignment guidance, and later search/import depth.

### Phase 4: Tracking
**Goal**: Users can record what they spend and where they go, and see a summary of expenses by category
**Depends on**: Phase 2
**Requirements**: TRAK-01, TRAK-02, TRAK-03
**Success Criteria** (what must be TRUE):
  1. User can record an expense with amount (EUR), category, description, and optional linked place
  2. User can log a visit to a place with a timestamp and notes
  3. User can view an expense overview showing totals by category, filterable by trip or city
**Plans**: TBD

Current reality note:
The alpha now supports expense creation, visit logging, recent activity lists, and category totals. Follow-up work should focus on richer filters and better linking back into trips and cities.

### Phase 5: Admin
**Goal**: Users can manage OSM data imports, monitor system health, and configure personal preferences
**Depends on**: Phase 1
**Requirements**: ADMN-01, ADMN-02, ADMN-03, ADMN-04
**Success Criteria** (what must be TRUE):
  1. User can select a region and trigger an OSM data import from the admin UI
  2. User can see which regions have been imported, when, and the current import job status
  3. User can set personal preferences (interests, dietary filters, budget level) and they persist
  4. User can see system status: database size, API health indicator, and cronjob last-run timestamp
**Plans**: TBD

Current reality note:
Preferences, import inventory, system metrics, and recent import job history are now exposed in the API and frontend alpha. Imports now queue immediately and run in the background inside the app process; later work should focus on retry strategy, scheduled updates, and a richer import pipeline rather than more admin scaffolding.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

Note: Phase 5 (Admin) depends only on Phase 1 and can run concurrently with Phases 3-4 if needed.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Infrastructure | 0/3 | Deployable alpha foundation in repo | - |
| 2. Map + Save | 0/TBD | Alpha implementation started | - |
| 3. Trips | 0/TBD | Alpha implementation started | - |
| 4. Tracking | 0/TBD | Alpha implementation started | - |
| 5. Admin | 0/TBD | Alpha implementation started | - |
