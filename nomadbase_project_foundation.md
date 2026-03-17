# NomadBase
Personal Travel Companion

Version: 0.1
Status: Planning Phase
Owner: Project Founder

---

# 1. Product Vision

NomadBase is a **Personal Travel Companion** designed to help travelers explore, organize, and track their journeys in one unified tool.

The goal is not to build a generic travel app, but a **personal travel operating system** that supports travelers during their journey.

NomadBase focuses on four core capabilities:

- Discover places
- Save interesting locations
- Plan trips
- Track travel activities

The product should simplify travel by replacing the need for multiple apps.

---

# 2. Problem Statement

Travelers currently rely on many separate applications:

- Maps
- Restaurant discovery
- Hiking apps
- Expense tracking
- Travel planners
- Notes

Example tools currently used:

- Google Maps
- Komoot
- Splitwise
- Wanderlog

Problems with this approach:

- fragmented information
- multiple subscriptions
- poor personalization
- inefficient workflow during travel

NomadBase aims to unify these tasks.

---

# 3. Target Users

Primary Users:

- Backpackers
- Long-term travelers
- Digital nomads
- Solo travelers

Secondary Users:

- City travelers
- Outdoor enthusiasts
- Vegan travelers
- Minimalist travelers

---

# 4. Product Concept

NomadBase acts as a **personal travel dashboard**.

At any time the app should help answer:

Where am I?
What is around me?
What do I want to see?
What have I planned?
What have I already visited?
What have I spent?

---

# 5. Core App Modes

The application revolves around three main interaction modes.

## Discover Mode

Purpose:
Find interesting locations nearby.

Possible place types:

- attractions
- viewpoints
- parks
- restaurants
- cafes
- hiking spots
- cultural sites

Filters may include:

- vegan
- cheap
- nature
- museums
- hiking
- hidden gems

---

## Save Mode

Users can bookmark places.

Saved categories:

- Want to visit
- Favorites
- Visited

---

## Trip Mode

Trips can be organized into structured travel plans.

Example hierarchy:

Trip
  Country
  City
  Day
  Activities

---

## Track Mode

Optional travel tracking features:

- expenses
- visited places
- notes

---

# 6. MVP Scope

The first version should focus only on the core functionality.

MVP Features:

- interactive map
- display places from data sources
- filter places
- save places
- simple trip planning
- offline city caching

Features intentionally excluded from MVP:

- social networking
- booking integration
- community reviews
- messaging
- advanced AI recommendations

These may be considered later.

---

# 7. App Navigation Structure

To keep the UX simple, the app should contain only three primary sections.

## Map

Purpose:
Explore nearby locations.

Features:

- map view
- markers for places
- filtering

---

## Saved

Purpose:
Access stored locations.

Features:

- favorites
- want to visit
- visited places

---

## Trips

Purpose:
Organize travel plans.

Features:

- create trips
- assign cities
- add places to itinerary

---

# 8. Technical Architecture Overview

## Application Type

Progressive Web App (PWA)

Reasons:

- faster development
- single codebase
- installable
- no app store dependency

---

## Frontend

Framework stack:

Vue
Vite
Pinia
Vue Router

PWA components:

Service Worker
Offline cache

---

## Map Engine

Leaflet

Map data:

OpenStreetMap

---

## Backend

Framework:

FastAPI

Backend services:

places service
trip service
recommendation service

---

## Database

PostgreSQL with PostGIS

Key capabilities:

- geospatial queries
- distance calculations
- radius search

---

## Cache Layer

Redis

Usage:

- API caching
- recommendation caching

---

# 9. Offline Strategy

Offline capability is critical for travel use cases.

When a user selects a city:

The app downloads:

- points of interest
- map tiles
- essential images

Data is stored locally using:

IndexedDB

This allows discovery and planning without internet connection.

---

# 10. Data Sources

## OpenStreetMap

Primary data source for places.

Example tags:

tourism=attraction
amenity=restaurant
tourism=viewpoint
leisure=park

Data can be accessed through:

Overpass API

---

## Wikipedia

Used for:

- descriptions
- background information
- images

---

## Wikidata

Used for structured metadata.

---

## Vegan Location Tags

OpenStreetMap supports dietary tags such as:

diet:vegan=yes
diet:vegetarian=yes

These allow filtering for vegan-friendly locations.

---

# 11. Data Pipeline Concept

Data flow may follow this pattern:

External APIs
→ Data extraction
→ Data cleaning
→ Database storage
→ Backend API
→ Frontend display

---

# 12. Development Strategy

The product will initially be built for personal use.

The developer will test the app during a **4 month travel period**.

During this time a "Travel Pain Log" should be maintained.

This log records:

- missing features
- usability problems
- discovery issues
- planning inefficiencies

These insights will guide future development.

---

# 13. Possible Monetization (Future)

The product initially focuses on usability rather than monetization.

Possible future models include:

One-time purchase

Freemium features

Offline travel packs

Affiliate links for hotels and tours

---

# 14. Naming Options

Working names considered:

NomadBase
NomadPath
NomadWay
Waypoint Companion
Wayfinder

Current working title:

NomadBase

---

# 15. Key Product Principles

The application should follow these design principles:

- simplicity
- minimal navigation
- offline-first thinking
- personal utility
- modular growth

---

# 16. Non-Goals (For Now)

The following features are intentionally excluded in early versions:

- social media features
- messaging
- booking platform
- travel marketplace
- influencer style travel feed

NomadBase focuses on **personal travel assistance**, not social networking.

---

# 17. Future Ideas (Not MVP)

Possible later expansions:

AI travel recommendations
automatic route planning
travel statistics
community shared locations
travel journals
photo integration
smart itinerary generation

These should only be considered after a stable MVP.

---

# 18. Open Questions

Items requiring further planning:

- final data model
- OSM import strategy
- offline map tile management
- place recommendation logic
- data deduplication strategy
- scalable POI storage

---

# 19. Next Planning Steps

The following planning documents should be created next:

1. Data Model Specification
2. User Flow Documentation
3. API Specification
4. Map Rendering Strategy
5. Offline Storage Design
6. Codex Implementation Task List

---

# End of Document