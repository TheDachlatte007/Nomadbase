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

### Phase 2: Trip-scoped saves
- Add `trip_id` to saved places.
- Allow one place to be saved globally or for a specific trip.
- Show trip-specific shortlists such as `food`, `churches`, `nature`, `backup options`.
- Keep the map save flow lightweight: default to the active trip, but allow switching back to a global shortlist.

### Phase 3: Route overview
- Let a trip define an ordered city route.
- Generate a simple per-city overview:
  - top places by category
  - food / coffee / vegan / nature / culture counts
  - saved shortlist and recent notes

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

## Constraints

- Do not depend on local Docker for verification.
- Keep deployment simple enough for Portainer.
- Prefer owned/cached data over runtime dependency on external APIs.
