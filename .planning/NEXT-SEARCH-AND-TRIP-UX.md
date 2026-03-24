# Next Search And Trip UX

## Current Product Direction

NomadBase should become a trip-scoped travel database first:
- one trip defines cities, participants, expenses, and saved places
- search should answer intent queries like `vegan restaurant toronto`
- mobile use is the default interaction model

## What Was Just Prioritized

1. Search quality over more raw place volume.
- Interpret intent words such as `vegan`, `vegetarian`, `restaurant`, `coffee`, `church`.
- Rank results by diet/type/location relevance instead of mostly alphabetic order.
- Keep broad text intent separate from strict tag filters so `vegan restaurant toronto` still finds candidates.
- Keep OpenStreetMap as the primary source for now because the product goal is an owned database.

2. Editable shared expenses.
- Existing expenses must be editable after the fact.
- Participants can be added later and old expenses must then be re-split cleanly.
- Mobile editing should reuse the existing form rather than opening a complex modal.

3. Mobile-first hardening.
- Button groups and list cards must stack cleanly.
- Long participant names, place names, and metadata should wrap instead of overflowing.
- Split map controls into query, trip scope, and imported region scope.
- Keep secondary actions like saving places collapsible on small screens.

## Recommended Next Phases

### Phase 1: Search v1.1
- Expand semantic parsing for place intents and amenities.
- Add better ranking for exact region matches and diet tags.
- Improve place cards so imported OSM metadata is surfaced more clearly.

Status:
- Done in alpha-plus form.
- Search now treats words like `vegan` and `vegetarian` as soft intent signals instead of hard text filters.
- Region matches and city-context matches are ranked more strongly.
- Place cards now expose more useful imported facts directly in the UI.

### Phase 2: Trip-scoped saves
- Done in alpha.
- Saved places can live globally or inside one trip.
- The remaining follow-up is better editing and assignment UX, not the base data model.

### Phase 3: Route overview
- Now started in alpha.
- Trips can define an ordered city route.
- Trip saves can now be assigned to one of the trip cities.
- The current overview covers:
  - ordered route
  - saved count per city
  - favorites / want-to-visit counts
  - lightweight place-type summary
  - trip planner map/list view with grouped city saves
  - visibility for unassigned trip saves
- Remaining follow-up:
  - better city-level notes and highlights
  - optional auto-suggestions for unassigned trip saves

### Phase 4: Live search enrichment
- Continue importing OSM into the local DB as the canonical dataset.
- Add optional live enrichment only where local coverage is weak.
- Candidate future sources:
  - official places APIs for better business metadata
  - Wikipedia / Wikidata for descriptions and context

### Phase 5: Lightweight AI workflow
- Keep AI out of the hot path for core CRUD/search.
- Use it as an assistant layer:
  - summarize a route
  - suggest category mixes per city
  - automate repetitive trip setup

## Next Recommended Build Order

1. Trip planner follow-up
- Add city notes so each stop can hold intent, logistics, and reminders.
- Add richer city highlights in the planner, not just counts.
- Suggest likely city assignment targets for unassigned trip saves.
- Keep the whole flow mobile-first and low-friction.

2. Import pipeline follow-up
- Keep the current synchronous import path, but harden the admin experience around it.
- Improve visibility for recent import runs and make failure states clearer.
- Leave background queueing as a later step unless sync imports become an actual pain point.

3. Deploy and smoke-check follow-up
- Extend the smoke script when useful, but keep it tiny and reliable.
- Focus on checks that catch real Portainer regressions quickly.

4. Optional enrichment later
- Add external context only where the owned OSM dataset is weak.
- Keep third-party lookups out of the hot path.

## Sequential Execution Plan

This is the current ordered work queue. Work should move top to bottom unless a blocker appears.

### Item 1: Trip planner v1.1
- City notes editable from the trip planner.
- Better city-level summary cards.
- Suggested placement for unassigned trip saves.
- Success criteria:
  - a city can store notes
  - the planner shows those notes and stronger highlights
  - unassigned trip saves are no longer just a flat bucket with no direction
Status: done

### Item 2: Import admin v1.1
- Keep recent import jobs visible and easier to read.
- Tighten import feedback and status language.
- Success criteria:
  - import runs are easy to inspect after the fact
  - a failed import is obvious without opening logs
Status: done

### Item 3: Deploy guardrails
- Expand smoke coverage only where it adds signal.
- Keep docs aligned with the real rollout flow.
- Success criteria:
  - the deploy checklist stays short
  - core alpha failures are quickly visible
Status: done for the current alpha scope

### Item 4: Import execution v2
- Move city imports out of the blocking request path.
- Keep the admin surface responsive while jobs run in the background.
- Success criteria:
  - import requests return quickly with a queued job
  - the UI can poll a single import job and show queued/running/completed states
  - recent job history stays useful after page reloads
Status: done

### Item 5: Richer trip intelligence
- Turn the planner into a decision surface, not just a storage view.
- Add route-level highlights plus city-level discovery suggestions from the owned places dataset.
- Success criteria:
  - the trip overview summarizes route coverage and rough route distance
  - each city shows useful next discovery candidates that are not already saved
  - a discovery candidate can be saved straight into the current city without leaving the planner
Status: done

### Item 6: Map surface v1.1
- Strengthen the map as the main discovery surface instead of leaving route context trapped in the planner.
- Tie active trip routing directly into the map and fix the inline import flow against the new background-job model.
- Success criteria:
  - the active trip route is visible directly on the map page
  - city chips can jump discovery to a planned stop quickly on mobile
  - inline imports work again with queued background jobs instead of the old synchronous flow
Status: done

### Item 7: Import quality + coverage
- Make the import core more resilient before building deeper data workflows on top.
- Normalize imported region names, add Overpass endpoint fallbacks, and broaden OSM category coverage without blowing up the surface area.
- Success criteria:
  - imports normalize to a more stable canonical region name
  - import jobs survive a single Overpass endpoint outage better
  - imported data includes a slightly wider spread of useful travel places inside the existing alpha model
Status: done

## Constraints

- Do not depend on local Docker for verification.
- Keep deployment simple enough for Portainer.
- Prefer owned/cached data over runtime dependency on external APIs.

## Baseline Hardening Sprint

This is the next ordered build queue for the two-week pre-trip window.
The goal is not feature sprawl. The goal is that one real trip can be created,
prepared offline enough, and used daily without obvious friction.

### Item 8: Trip coverage and import readiness
- Show local data coverage per trip city directly in the planner.
- Let the planner queue imports for one city or all weak cities.
- Success criteria:
  - every stop shows whether local place coverage is ready, usable, thin, or missing
  - missing or thin cities can be queued for import without leaving the trip flow
  - route preparation becomes more deterministic before departure
Status: done

### Item 9: Shared trip workflow hardening
- Tighten the most common in-trip daily actions:
  - edit and re-split expenses cleanly
  - reduce friction when trip participants change
  - keep mobile forms and summary cards compact and reliable
- Success criteria:
  - expense editing feels like part of the main flow, not a hidden edge case
  - users can recover from a changed group setup without data confusion
  - key tracking actions stay comfortable on mobile
Status: done

### Item 10: Offline-first trip confidence
- Make the app clearer about what is already cached locally versus still dependent on fresh imports.
- Tighten the baseline deploy/smoke checks around trip, tracking, and import readiness.
- Success criteria:
  - a user can tell whether a trip is ready to use on the road
  - the smoke script checks the most important baseline endpoints
  - Portainer deploy regressions are easier to spot quickly
Status: done

### Item 11: Owned data depth follow-up
- Push the owned-data model further:
  - broader region coverage
  - cleaner route-wide import preparation
  - richer descriptions only where they add practical value
- Success criteria:
  - route planning does not rely on a lucky narrow import set
  - the local database becomes progressively more useful per trip
Status: done

## Follow-up Queue

This is the next compact queue after the baseline hardening sprint.
It keeps the same rule: practical trip readiness first, no big-bang rewrites.

### Item 12: Core trip coverage
- Make route readiness care about trip basics, not only total POI counts.
- Track whether each city has enough local `food`, `stay`, `essentials`, and `transport` coverage.
- Success criteria:
  - the planner can show which cities still miss practical route basics
  - route readiness stops overstating quality when a city has many POIs but poor trip utility
Status: done

### Item 13: Import preparation automation
- Move import queueing closer to the trip workflow itself.
- Auto-queue imports when a new city is added and allow the planner to prep stale or weak stops in one step.
- Success criteria:
  - city creation does not depend on a frontend-only side effect to start local data prep
  - the trip planner can prep weak or stale stops quickly before departure
Status: done

### Item 14: Homeserver deploy defaults
- Add the first meaningful deploy knobs without making the alpha stack painful.
- Keep permissive defaults for local alpha, but support tightening CORS and trusted hosts for real self-hosting.
- Success criteria:
  - deploy docs and env examples match the actual app behavior
  - the app can be hardened for a homeserver without code edits
Status: done

### Item 15: MapLibre migration
- Replace the temporary Leaflet map surface with MapLibre GL JS.
- Keep the product closer to its intended long-term map architecture instead of polishing the temporary stack forever.
- Success criteria:
  - the discovery map and trip planner both run on MapLibre
  - route overlays and place markers still work in the main trip flows
  - the map architecture is now aligned with the long-term viewport-first direction
Status: done

### Item 16: Viewport-driven discovery
- Stop treating the map as only a visual shell around generic place queries.
- Let the active viewport shape discovery results so the map feels more like a real trip-planning surface.
- Success criteria:
  - map place queries can be filtered by bbox
  - moving the map can reload places for the current view
  - route-oriented map exploration gets tighter without abandoning the owned dataset
Status: done

### Item 17: Trip readiness preflight
- Turn the route overview into a real pre-trip checklist instead of just a route summary.
- Make blockers, next steps, and route-prep actions visible where trip planning already happens.
- Success criteria:
  - each active trip exposes a clear readiness state for the first real trip run
  - planner and map flows can queue route prep directly without admin detours
  - the pre-trip story is visible on mobile without opening several screens
Status: done

### Item 18: Daily-use tracking polish
- Remove a bit more friction from the expense flow the user will hit on the road every day.
- Add low-friction presets for common categories and shared-split shortcuts.
- Success criteria:
  - the expense form is quicker to fill on mobile
  - payer and split controls feel less fiddly in repeated daily use
Status: done
