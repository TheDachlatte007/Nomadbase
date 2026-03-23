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

## Constraints

- Do not depend on local Docker for verification.
- Keep deployment simple enough for Portainer.
- Prefer owned/cached data over runtime dependency on external APIs.
