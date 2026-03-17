# NomadBase – Data Model & System Design (Agent-Friendly)

Version: 0.1
Status: Planning
Role: This document is intended for AI agents and developers to design and implement the system.

IMPORTANT:
You are encouraged to:
- question assumptions
- suggest improvements
- propose better architectures
- highlight scalability or performance issues
- ask clarifying questions before implementing unclear parts

---

# 1. Goal of This Document

Define a **flexible, scalable data model and system architecture** for NomadBase.

The system must support:

- travel discovery
- trip planning
- place saving
- offline usage
- future extensibility

---

# 2. Core Design Principles

The system should follow:

- modular design
- offline-first thinking
- scalability for large POI datasets
- fast geospatial queries
- minimal complexity for MVP

---

# 3. Core Entities (Conceptual Level)

These are logical entities, not final DB schemas.

---

## 3.1 Trip

Represents a full journey.

Attributes:

- id
- name
- start_date
- end_date
- notes

Relations:

- contains multiple cities
- contains multiple saved places

---

## 3.2 City

Represents a location where the user stays.

Attributes:

- id
- name
- country
- coordinates (lat, lon)

Relations:

- belongs to a trip
- contains places (via geographic queries)
- can be cached offline

---

## 3.3 Place (POI)

Represents any point of interest.

Attributes:

- id
- name
- type (restaurant, attraction, park, etc.)
- coordinates
- tags (vegan, cheap, nature, etc.)
- description (optional)
- source (OSM, Wikipedia, etc.)

Important:

This entity will likely be very large (100k+ entries).

---

## 3.4 SavedPlace

Represents user interaction with a place.

Attributes:

- id
- place_id
- user_state:
  - WANT_TO_VISIT
  - VISITED
  - FAVORITE

Optional:

- rating
- notes

---

## 3.5 Visit

Represents an actual visit event.

Attributes:

- id
- place_id
- timestamp
- notes

---

## 3.6 Expense

Represents a cost entry.

Attributes:

- id
- amount
- currency
- category
- description
- linked_place (optional)

---

## 3.7 User Preferences

Represents personalization.

Attributes:

- vegan
- budget_level
- interests (nature, museums, nightlife, etc.)

---

# 4. Data Relationships

High-level relationships:

Trip → City → Place

User interacts with Place via:

- SavedPlace
- Visit
- Expense

---

# 5. Data Sources

Primary:

- OpenStreetMap (POIs)

Secondary:

- Wikipedia
- Wikidata

---

## Agent Task

Evaluate:

- Should data be stored fully or partially cached?
- Should external APIs be queried live or pre-ingested?

---

# 6. POI Data Strategy (Critical Section)

Important considerations:

- POI dataset may exceed 100k+ entries per region
- performance must remain smooth on map rendering

---

## Open Questions for Agent

- Should POIs be stored in full or filtered?
- Should we pre-filter by categories?
- Should we store bounding boxes per city?
- Should we use clustering or tile-based loading?

---

# 7. Geospatial Requirements

System must support:

- nearby places query
- radius search
- sorting by distance
- filtering by tags

---

## Agent Task

Propose:

- optimal PostGIS indexing strategy
- query optimization
- performance improvements

---

# 8. Offline Storage Strategy

The system must allow:

- city-level offline usage

---

## Proposed Flow

When user selects a city:

Download:

- POIs
- map tiles
- minimal images

Store in:

- IndexedDB

---

## Agent Task

Evaluate:

- data size limits
- compression strategies
- caching invalidation
- sync strategy when reconnecting

---

# 9. API Design (Conceptual)

Endpoints may include:

GET /places
GET /places/nearby
GET /trips
POST /trips
POST /saved_places
GET /saved_places

---

## Agent Task

Propose:

- REST vs GraphQL
- endpoint structure
- pagination strategy
- caching strategy

---

# 10. Map Rendering Challenges

Known issues:

- too many markers
- performance degradation
- mobile device limitations

---

## Agent Task

Suggest:

- marker clustering
- tile-based rendering
- lazy loading strategies

---

# 11. Data Pipeline

Possible pipeline:

External APIs
→ ingestion script
→ cleaning
→ database

---

## Agent Task

Propose:

- ingestion architecture
- update frequency
- deduplication strategy
- data enrichment

---

# 12. Scalability Considerations

Future risks:

- large datasets
- slow queries
- offline storage limits
- API latency

---

## Agent Task

Identify:

- bottlenecks
- scaling strategies
- caching layers

---

# 13. MVP Constraints

For MVP:

- keep system simple
- avoid over-engineering
- prioritize usability over completeness

---

# 14. Questions for the Agent

Before implementation, the agent should answer:

1. What is the simplest working architecture?
2. What is the biggest technical risk?
3. How to handle large POI datasets efficiently?
4. What should NOT be built yet?
5. What can be deferred?

---

# 15. Expected Output from Agent

The agent should produce:

- refined data model
- proposed database schema
- API design
- system architecture
- implementation plan

---

# End of Document