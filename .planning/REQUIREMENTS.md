# Requirements: NomadBase

**Defined:** 2026-03-17
**Core Value:** A single app that answers: Where am I? What's around me? What do I want to see? What have I planned? What have I visited? What have I spent?

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Map/Discover

- [ ] **MAP-01**: User can view interactive map showing POIs in current viewport (MapLibre GL JS + OpenStreetMap)
- [ ] **MAP-02**: User can filter POIs by type (restaurants, attractions, parks, cafes, hiking spots, viewpoints, cultural sites)
- [ ] **MAP-03**: User can apply lifestyle filters (vegan, cheap, nature, hidden gems)

### Save

- [ ] **SAVE-01**: User can save/bookmark places with status: Want to Visit, Visited, Favorite
- [ ] **SAVE-02**: User can add personal notes to saved places

### Trips

- [ ] **TRIP-01**: User can create trips with name, start/end date, and notes
- [ ] **TRIP-02**: User can assign cities to a trip
- [ ] **TRIP-03**: User can add saved places to a trip city
- [ ] **TRIP-04**: User can view trip as map with pins + side list of planned places

### Tracking

- [ ] **TRAK-01**: User can record expenses (amount in EUR, category, description, optional linked place)
- [ ] **TRAK-02**: User can log visits (place, timestamp, notes)
- [ ] **TRAK-03**: User can view expense overview (sums by category, per trip/city)

### Admin

- [ ] **ADMN-01**: User can trigger OSM data import for specific regions
- [ ] **ADMN-02**: User can view import status (which regions imported, last update timestamp)
- [ ] **ADMN-03**: User can set preferences (interests, dietary filters, budget level)
- [ ] **ADMN-04**: User can view system status (DB size, API health, cronjob status)

### Infrastructure

- [ ] **INFR-01**: Docker Compose setup running FastAPI + PostgreSQL with PostGIS
- [ ] **INFR-02**: OSM data pipeline: Geofabrik extract import + scheduled cronjob for updates
- [ ] **INFR-03**: REST API with FastAPI endpoints for all feature areas
- [ ] **INFR-04**: PWA foundation: installable, service worker scaffold, mobile-first responsive

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Map Enhancements

- **MAP-04**: Marker clustering for dense POI areas
- **MAP-05**: Offline map tile caching per city

### Save Enhancements

- **SAVE-03**: Star rating for visited places

### Authentication

- **AUTH-01**: User account creation with email/password
- **AUTH-02**: Session management and login persistence
- **AUTH-03**: Multi-user data isolation

### Advanced Features

- **ADVN-01**: AI-powered travel recommendations
- **ADVN-02**: Automatic route planning between trip places
- **ADVN-03**: Travel statistics and analytics dashboard
- **ADVN-04**: Travel journal with photo integration
- **ADVN-05**: Multi-currency expense tracking with conversion

### Performance

- **PERF-01**: Redis cache layer for API responses

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Social networking / messaging | Personal tool, not a social platform |
| Booking integration | Not a marketplace |
| Community reviews / UGC | No user-generated content in early versions |
| Travel marketplace | Focus on personal utility |
| Influencer-style travel feed | Against core design principles |
| Mobile native app | PWA covers mobile use case |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFR-01 | Phase 1 | Alpha |
| INFR-02 | Phase 1 | Pending |
| INFR-03 | Phase 1 | Alpha |
| INFR-04 | Phase 1 | Alpha |
| MAP-01 | Phase 2 | Pending |
| MAP-02 | Phase 2 | Partial alpha |
| MAP-03 | Phase 2 | Pending |
| SAVE-01 | Phase 2 | Alpha |
| SAVE-02 | Phase 2 | Alpha |
| TRIP-01 | Phase 3 | Alpha |
| TRIP-02 | Phase 3 | Alpha |
| TRIP-03 | Phase 3 | Pending |
| TRIP-04 | Phase 3 | Pending |
| TRAK-01 | Phase 4 | Alpha |
| TRAK-02 | Phase 4 | Alpha |
| TRAK-03 | Phase 4 | Alpha |
| ADMN-01 | Phase 5 | Pending |
| ADMN-02 | Phase 5 | Alpha |
| ADMN-03 | Phase 5 | Alpha |
| ADMN-04 | Phase 5 | Alpha |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0

---
*Requirements defined: 2026-03-17*
*Last updated: 2026-03-17 after roadmap creation — all 20 requirements mapped*
