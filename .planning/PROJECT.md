# NomadBase

## What This Is

NomadBase is a personal travel companion — a unified travel operating system that replaces the need for Google Maps, Komoot, Splitwise, Wanderlog, and other fragmented travel tools. Built as a mobile-first Progressive Web App, it helps travelers discover places, save interesting locations, plan trips, and track expenses and visits — all in one tool. Initially built for personal use during a 4-month journey through Europe and Canada.

## Core Value

A single app that answers: Where am I? What's around me? What do I want to see? What have I planned? What have I visited? What have I spent?

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

- [ ] Interactive map showing all nearby POIs with filter toggles (by type: attractions, viewpoints, parks, restaurants, cafes, hiking, cultural)
- [ ] Dietary and lifestyle filters (vegan, cheap, nature, hidden gems)
- [ ] Save/bookmark places with states: Want to Visit, Visited, Favorite
- [ ] Trip planning with map + side list view (Trip > Cities > Places)
- [ ] Expense tracking in EUR (amount, category, description, optional linked place)
- [ ] Visit logging (place, timestamp, notes)
- [ ] POI data pre-ingested from OpenStreetMap via Geofabrik extracts (Europe + Canada)
- [ ] Data import system: CLI tool + cronjob + admin UI trigger
- [ ] Admin panel: import trigger, import status, user preferences, system status
- [ ] User preference settings (interests, dietary filters, budget level)
- [ ] MapLibre GL JS map with marker clustering for large POI datasets
- [ ] Mobile-first responsive design
- [ ] Docker Compose deployment (FastAPI + PostgreSQL)

### Out of Scope

- Social networking / messaging — personal tool, not a social platform
- Booking integration — not a marketplace
- Community reviews — no user-generated content for now
- AI travel recommendations — defer until stable MVP
- Offline city caching — nice-to-have, not v1 critical (usually has internet)
- Multi-user authentication — single-user MVP, auth foundation added later
- Redis cache layer — unnecessary for single-user traffic
- Mobile native app — PWA covers mobile use case

## Context

The developer will test NomadBase during a 4-month trip: 6 weeks through Europe followed by 2.5 months across Canada. This real-world usage will generate a "Travel Pain Log" to guide future development. The app must be functional before departure (1-2 month build window).

The app runs on a homeserver accessed via VPN (Tailscale/WireGuard) while traveling. POI data for Europe and Canada will be pre-imported from OpenStreetMap Geofabrik extracts before the trip.

Primary data sources:
- OpenStreetMap (POIs via Overpass API tags: tourism=attraction, amenity=restaurant, tourism=viewpoint, leisure=park, diet:vegan=yes, etc.)
- Wikipedia/Wikidata (descriptions, background info, images)

Target users (future): Backpackers, long-term travelers, digital nomads, solo travelers. Secondary: city travelers, outdoor enthusiasts, vegan travelers.

## Constraints

- **Timeline**: App must be usable within 1-2 months (before trip departure)
- **Tech Stack**: Vue 3 + Vite + Pinia + Vue Router (frontend), FastAPI (backend), PostgreSQL + PostGIS (database), MapLibre GL JS (map)
- **Deployment**: Docker Compose on homeserver, VPN access
- **Data Volume**: 100k+ POIs for Europe + Canada regions — requires performant geospatial indexing
- **Single User**: No auth complexity in MVP, but data model should not preclude multi-user later
- **Currency**: All expenses tracked in EUR (single currency)
- **Design**: Mobile-first PWA, three primary sections: Map, Saved, Trips

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| MapLibre GL JS over Leaflet | WebGL-based, native clustering, handles 100k+ POIs performantly | — Pending |
| PostgreSQL + PostGIS | Industry standard for geodata, used by OSM itself, mature spatial indexes | — Pending |
| No Redis in MVP | Single-user traffic doesn't justify cache layer complexity | — Pending |
| Pre-ingest OSM data | More control, enables future offline, Geofabrik extracts are free and current | — Pending |
| Docker Compose deployment | Single command setup, easy updates, reproducible environment | — Pending |
| Mobile-first design | Primary usage is on phone while traveling | — Pending |
| Single currency (EUR) | Simplifies expense tracking, multi-currency deferred | — Pending |
| Offline as nice-to-have | Usually has internet, full offline adds significant complexity | — Pending |

---
*Last updated: 2026-03-17 after initialization*
