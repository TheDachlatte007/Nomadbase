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

1. Trip planner follow-up: city highlights, city notes, and smarter unassigned-save suggestions.
2. Import pipeline follow-up: background execution, retries, and maybe queueing if sync imports become painful.
3. Smoke-test scripts can be extended with richer deployment assertions after each Portainer rollout.
4. Optional live enrichment for weakly-described places via Wikipedia / Wikidata style context.

## Constraints

- Do not depend on local Docker for verification.
- Keep deployment simple enough for Portainer.
- Prefer owned/cached data over runtime dependency on external APIs.
