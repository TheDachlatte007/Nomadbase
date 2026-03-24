import math
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from geoalchemy2 import WKTElement
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.city import City
from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.models.import_job import ImportJob
from app.models.place import Place
from app.models.saved_place import SavedPlace
from app.models.trip import Trip
from app.models.trip_participant import TripParticipant
from app.schemas.trip import (
    TripCoverageImportRequest,
    TripCoverageImportResponse,
    TripCityCreateRequest,
    TripCityReorderRequest,
    TripCityUpdateRequest,
    TripCreateRequest,
    TripListResponse,
    TripOverviewResponse,
    TripParticipantCreateRequest,
    TripResponse,
    TripUpdateRequest,
)
from app.services.import_jobs import enqueue_import_jobs

router = APIRouter()

DISCOVERY_TYPE_BONUSES = {
    "attraction": 22,
    "viewpoint": 20,
    "cultural": 20,
    "park": 16,
    "hiking": 16,
    "restaurant": 14,
    "cafe": 12,
}


def _parse_uuid(value: str, field_name: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} must be a valid UUID",
        ) from exc


def _distance_km(
    lat1: float | None,
    lon1: float | None,
    lat2: float | None,
    lon2: float | None,
) -> float | None:
    if None in {lat1, lon1, lat2, lon2}:
        return None

    earth_radius_km = 6371.0
    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    return earth_radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _suggest_place_for_city(city_entry: dict, place_payload: dict) -> int:
    score = 0
    region = (place_payload.get("region") or "").lower()
    city_name = (city_entry.get("name") or "").lower()
    country = (city_entry.get("country") or "").lower()

    if city_name and city_name in region:
        score += 110
    if country and country in region:
        score += 35

    distance = _distance_km(
        city_entry.get("lat"),
        city_entry.get("lon"),
        place_payload.get("lat"),
        place_payload.get("lon"),
    )
    if distance is not None:
        if distance <= 8:
            score += 90
        elif distance <= 25:
            score += 60
        elif distance <= 80:
            score += 28

    return score


def _build_city_highlights(city_entry: dict) -> list[str]:
    highlights: list[str] = []
    if city_entry.get("saved_count"):
        highlights.append(f"{city_entry['saved_count']} saved places in this stop")
    if city_entry.get("favorite_count"):
        highlights.append(f"{city_entry['favorite_count']} favorites already marked")
    if city_entry.get("want_to_visit_count"):
        highlights.append(f"{city_entry['want_to_visit_count']} still on the shortlist")

    place_type_counts = city_entry.get("place_type_counts") or {}
    if place_type_counts:
        top_types = (
            sorted(place_type_counts.items(), key=lambda item: (-item[1], item[0]))[:2]
        )
        highlights.append(
            "Top categories: "
            + " · ".join(f"{place_type} {count}" for place_type, count in top_types)
        )

    if city_entry.get("preview_places"):
        highlights.append("Examples: " + " · ".join(city_entry["preview_places"][:3]))

    return highlights[:4]


def _build_route_label(city_names: list[str]) -> str:
    if not city_names:
        return "No route yet"
    if len(city_names) <= 4:
        return " -> ".join(city_names)
    return " -> ".join(city_names[:3]) + f" -> +{len(city_names) - 3} more"


def _build_route_highlights(
    *,
    city_count: int,
    participant_count: int,
    route_distance_km: float | None,
    assigned_saved_places: int,
    unassigned_saved_places: int,
    cities_without_places: int,
    top_place_types: dict[str, int],
) -> list[str]:
    highlights = [f"{city_count} stops planned for {participant_count or 1} traveler(s)"]

    if route_distance_km is not None:
        highlights.append(f"Approx. {round(route_distance_km)} km between mapped stops")
    if assigned_saved_places:
        highlights.append(f"{assigned_saved_places} places already tied to a city")
    if unassigned_saved_places:
        highlights.append(f"{unassigned_saved_places} saved places still need a city")
    if cities_without_places:
        highlights.append(f"{cities_without_places} stops still need their first shortlist")
    if top_place_types:
        top_entries = sorted(
            top_place_types.items(), key=lambda item: (-item[1], item[0])
        )[:3]
        highlights.append(
            "Route mix: "
            + " · ".join(f"{place_type} {count}" for place_type, count in top_entries)
        )

    return highlights[:5]


def _coverage_level(local_place_count: int) -> str:
    if local_place_count >= 120:
        return "ready"
    if local_place_count >= 35:
        return "usable"
    if local_place_count >= 1:
        return "thin"
    return "missing"


def _build_coverage_summary(level: str, local_place_count: int, import_region_hint: str) -> str:
    if level == "ready":
        return f"{local_place_count} local places already cover {import_region_hint}."
    if level == "usable":
        return f"{local_place_count} local places exist for {import_region_hint}, enough for basic trip use."
    if level == "thin":
        return f"Only {local_place_count} local places are available for {import_region_hint}; importing more is recommended."
    return f"No local places are cached for {import_region_hint} yet."


def _build_discovery_reason(
    city_entry: dict,
    *,
    place_type: str,
    region: str | None,
    tags: dict | None,
    distance_km: float | None,
) -> str:
    reasons: list[str] = []
    city_name = (city_entry.get("name") or "").lower()
    normalized_region = (region or "").lower()
    tags = tags or {}

    if distance_km is not None:
        if distance_km <= 3:
            reasons.append("Very close to this stop")
        elif distance_km <= 10:
            reasons.append("Easy detour from the city")
        elif distance_km <= 25:
            reasons.append("Reachable side trip")

    if city_name and city_name in normalized_region:
        reasons.append("Matches the imported city region")

    if tags.get("diet:vegan") == "yes" or tags.get("diet:vegetarian") == "yes":
        reasons.append("Has vegan or vegetarian signal")
    elif place_type in {"restaurant", "cafe"}:
        reasons.append("Useful food stop candidate")
    elif place_type in {"attraction", "cultural", "viewpoint"}:
        reasons.append("Good sightseeing pick")
    elif place_type in {"park", "hiking"}:
        reasons.append("Good outdoor break")

    return " · ".join(reasons[:2]) or "Relevant for this route stop"


async def _load_city_discovery_candidates(
    db: AsyncSession,
    city_entry: dict,
    excluded_place_ids: set[UUID],
) -> list[dict]:
    city_name = city_entry.get("name")
    country = city_entry.get("country")
    lat = city_entry.get("lat")
    lon = city_entry.get("lon")
    city_name_pattern = f"%{city_name.lower()}%" if city_name else None
    country_pattern = f"%{country.lower()}%" if country else None

    stmt = select(
        Place.id,
        Place.name,
        Place.place_type,
        Place.description,
        Place.region,
        Place.tags,
        func.ST_Y(Place.location).label("lat"),
        func.ST_X(Place.location).label("lon"),
    )

    if excluded_place_ids:
        stmt = stmt.where(Place.id.notin_(excluded_place_ids))

    filters = []
    if city_name_pattern:
        filters.append(func.lower(func.coalesce(Place.region, "")).like(city_name_pattern))
        filters.append(func.lower(Place.name).like(city_name_pattern))
    if country_pattern:
        filters.append(func.lower(func.coalesce(Place.region, "")).like(country_pattern))
    if lat is not None and lon is not None:
        city_point = WKTElement(f"POINT({lon} {lat})", srid=4326)
        filters.append(func.ST_DistanceSphere(Place.location, city_point) <= 25000)

    if filters:
        stmt = stmt.where(or_(*filters))

    rows = (await db.execute(stmt.limit(40))).all()
    candidates: list[dict] = []
    for row in rows:
        distance_km = _distance_km(lat, lon, row.lat, row.lon)
        place_payload = {
            "region": row.region,
            "lat": float(row.lat),
            "lon": float(row.lon),
        }
        score = _suggest_place_for_city(city_entry, place_payload)
        score += DISCOVERY_TYPE_BONUSES.get(row.place_type, 8)
        tags = row.tags or {}
        if tags.get("diet:vegan") == "yes":
            score += 20
        elif tags.get("diet:vegetarian") == "yes":
            score += 12
        if row.description:
            score += 4

        if score < 35:
            continue

        candidates.append(
            {
                "place_id": str(row.id),
                "name": row.name,
                "place_type": row.place_type,
                "description": row.description,
                "region": row.region,
                "lat": float(row.lat),
                "lon": float(row.lon),
                "distance_km": round(distance_km, 1) if distance_km is not None else None,
                "score": score,
                "reason": _build_discovery_reason(
                    city_entry,
                    place_type=row.place_type,
                    region=row.region,
                    tags=tags,
                    distance_km=distance_km,
                ),
            }
        )

    candidates.sort(
        key=lambda item: (
            -item["score"],
            item["distance_km"] if item["distance_km"] is not None else 9999,
            item["name"].lower(),
        )
    )
    return candidates[:4]


async def _load_city_coverage(db: AsyncSession, city_entry: dict) -> dict:
    city_name = city_entry.get("name")
    country = city_entry.get("country")
    lat = city_entry.get("lat")
    lon = city_entry.get("lon")
    import_region_hint = f"{city_name}, {country}" if country else city_name
    city_name_pattern = f"%{city_name.lower()}%" if city_name else None
    country_pattern = f"%{country.lower()}%" if country else None

    region_conditions = []
    if city_name_pattern:
        region_conditions.append(func.lower(func.coalesce(Place.region, "")).like(city_name_pattern))
        region_conditions.append(func.lower(Place.name).like(city_name_pattern))
    if country_pattern:
        region_conditions.append(func.lower(func.coalesce(Place.region, "")).like(country_pattern))

    region_match_count = 0
    if region_conditions:
        region_match_count = int(
            await db.scalar(select(func.count()).select_from(Place).where(or_(*region_conditions)))
            or 0
        )

    nearby_place_count = 0
    if lat is not None and lon is not None:
        city_point = WKTElement(f"POINT({lon} {lat})", srid=4326)
        nearby_place_count = int(
            await db.scalar(
                select(func.count())
                .select_from(Place)
                .where(func.ST_DistanceSphere(Place.location, city_point) <= 25000)
            )
            or 0
        )

    last_imported_at = await db.scalar(
        select(func.max(ImportJob.finished_at)).where(
            ImportJob.status == "completed",
            func.lower(ImportJob.city) == (city_name or "").lower(),
            or_(
                ImportJob.country.is_(None),
                func.lower(func.coalesce(ImportJob.country, "")) == (country or "").lower(),
            ),
        )
    )
    active_job = (
        await db.execute(
            select(
                ImportJob.id,
                ImportJob.status,
                ImportJob.created_at,
            )
            .where(
                ImportJob.status.in_(("queued", "running")),
                func.lower(ImportJob.city) == (city_name or "").lower(),
                or_(
                    ImportJob.country.is_(None),
                    func.lower(func.coalesce(ImportJob.country, "")) == (country or "").lower(),
                ),
            )
            .order_by(ImportJob.created_at.desc())
            .limit(1)
        )
    ).first()

    local_place_count = max(region_match_count, nearby_place_count)
    level = _coverage_level(local_place_count)
    needs_import = level in {"thin", "missing"}

    return {
        "level": level,
        "local_place_count": local_place_count,
        "region_match_count": region_match_count,
        "nearby_place_count": nearby_place_count,
        "import_region_hint": import_region_hint,
        "summary": _build_coverage_summary(level, local_place_count, import_region_hint),
        "needs_import": needs_import,
        "last_imported_at": last_imported_at,
        "active_import_job_id": str(active_job.id) if active_job else None,
        "active_import_status": active_job.status if active_job else None,
        "active_import_created_at": active_job.created_at if active_job else None,
    }


async def _load_trip_payloads(
    db: AsyncSession, trip_ids: list[UUID] | None = None
) -> list[dict]:
    trip_stmt = select(
        Trip.id,
        Trip.name,
        Trip.start_date,
        Trip.end_date,
        Trip.notes,
        Trip.created_at,
        Trip.updated_at,
    ).order_by(Trip.created_at.desc())

    if trip_ids is not None:
        if not trip_ids:
            return []
        trip_stmt = trip_stmt.where(Trip.id.in_(trip_ids))

    trip_rows = (await db.execute(trip_stmt)).all()
    if not trip_rows:
        return []

    ordered_trip_ids = [row.id for row in trip_rows]
    trip_map = {
        row.id: {
            "id": str(row.id),
            "name": row.name,
            "start_date": row.start_date,
            "end_date": row.end_date,
            "notes": row.notes,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "cities": [],
            "participants": [],
        }
        for row in trip_rows
    }

    city_rows = (
        await db.execute(
            select(
                City.id,
                City.trip_id,
                City.name,
                City.country,
                City.created_at,
                City.updated_at,
                func.ST_Y(City.location).label("lat"),
                func.ST_X(City.location).label("lon"),
                City.sort_order,
                City.notes,
            )
            .where(City.trip_id.in_(ordered_trip_ids))
            .order_by(City.sort_order.asc(), City.created_at.asc(), City.name.asc())
        )
    ).all()
    for row in city_rows:
        trip_map[row.trip_id]["cities"].append(
            {
                "id": str(row.id),
                "name": row.name,
                "country": row.country,
                "lat": float(row.lat) if row.lat is not None else None,
                "lon": float(row.lon) if row.lon is not None else None,
                "sort_order": row.sort_order,
                "notes": row.notes,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
        )

    participant_rows = (
        await db.execute(
            select(
                TripParticipant.id,
                TripParticipant.trip_id,
                TripParticipant.name,
                TripParticipant.note,
                TripParticipant.created_at,
                TripParticipant.updated_at,
            )
            .where(TripParticipant.trip_id.in_(ordered_trip_ids))
            .order_by(TripParticipant.created_at.asc(), TripParticipant.name.asc())
        )
    ).all()
    for row in participant_rows:
        trip_map[row.trip_id]["participants"].append(
            {
                "id": str(row.id),
                "name": row.name,
                "note": row.note,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
        )

    return [trip_map[trip_id] for trip_id in ordered_trip_ids]


async def _load_trip_payload(db: AsyncSession, trip_id: UUID) -> dict:
    payloads = await _load_trip_payloads(db, [trip_id])
    if not payloads:
        raise HTTPException(status_code=404, detail="Trip not found")
    return payloads[0]


@router.get("/", response_model=TripListResponse)
async def list_trips(db: AsyncSession = Depends(get_db)):
    data = await _load_trip_payloads(db)
    return TripListResponse(
        data=data,
        total=len(data),
        message="Trips" if data else "No trips yet",
    )


@router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(payload: TripCreateRequest, db: AsyncSession = Depends(get_db)):
    trip = Trip(
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        notes=payload.notes,
    )
    db.add(trip)
    await db.commit()
    return TripResponse(**await _load_trip_payload(db, trip.id))


async def _load_trip_overview_payload(db: AsyncSession, trip_id: UUID) -> dict:
    trip = await db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    city_rows = (
        await db.execute(
            select(
                City.id,
                City.name,
                City.country,
                City.sort_order,
                func.ST_Y(City.location).label("lat"),
                func.ST_X(City.location).label("lon"),
                City.notes,
            )
            .where(City.trip_id == trip_id)
            .order_by(City.sort_order.asc(), City.created_at.asc(), City.name.asc())
        )
    ).all()

    city_map = {
        row.id: {
            "id": str(row.id),
            "name": row.name,
            "country": row.country,
            "sort_order": row.sort_order,
            "lat": float(row.lat) if row.lat is not None else None,
            "lon": float(row.lon) if row.lon is not None else None,
            "saved_count": 0,
            "want_to_visit_count": 0,
            "visited_count": 0,
            "favorite_count": 0,
            "place_type_counts": {},
            "preview_places": [],
            "notes": row.notes,
            "highlights": [],
            "places": [],
            "suggested_unassigned_places": [],
            "discovery_candidates": [],
            "coverage": None,
        }
        for row in city_rows
    }

    participant_count = (
        await db.scalar(
            select(func.count())
            .select_from(TripParticipant)
            .where(TripParticipant.trip_id == trip_id)
        )
        or 0
    )

    saved_rows = (
        await db.execute(
            select(
                SavedPlace.id.label("saved_place_id"),
                SavedPlace.place_id,
                SavedPlace.city_id,
                SavedPlace.status,
                SavedPlace.notes,
                Place.place_type,
                Place.name,
                Place.region,
                func.ST_Y(Place.location).label("lat"),
                func.ST_X(Place.location).label("lon"),
            )
            .join(Place, Place.id == SavedPlace.place_id)
            .where(SavedPlace.trip_id == trip_id)
            .order_by(SavedPlace.created_at.desc())
        )
    ).all()

    total_saved_places = len(saved_rows)
    assigned_saved_places = 0
    unassigned_saved_places = 0
    unassigned_places: list[dict] = []
    assigned_place_type_totals: dict[str, int] = {}
    saved_place_ids: set[UUID] = set()

    for row in saved_rows:
        saved_place_ids.add(row.place_id)
        place_payload = {
            "saved_place_id": str(row.saved_place_id),
            "place_id": str(row.place_id),
            "name": row.name,
            "place_type": row.place_type,
            "status": row.status,
            "notes": row.notes,
            "region": row.region,
            "lat": float(row.lat),
            "lon": float(row.lon),
            "city_id": str(row.city_id) if row.city_id else None,
            "city_name": city_map[row.city_id]["name"]
            if row.city_id and row.city_id in city_map
            else None,
        }
        if row.city_id is None or row.city_id not in city_map:
            unassigned_saved_places += 1
            unassigned_places.append(place_payload)
            continue

        assigned_saved_places += 1
        city_entry = city_map[row.city_id]
        city_entry["saved_count"] += 1
        if row.status == "want_to_visit":
            city_entry["want_to_visit_count"] += 1
        elif row.status == "visited":
            city_entry["visited_count"] += 1
        elif row.status == "favorite":
            city_entry["favorite_count"] += 1

        if row.place_type:
            city_entry["place_type_counts"][row.place_type] = (
                city_entry["place_type_counts"].get(row.place_type, 0) + 1
            )
            assigned_place_type_totals[row.place_type] = (
                assigned_place_type_totals.get(row.place_type, 0) + 1
            )
        if row.name and row.name not in city_entry["preview_places"]:
            city_entry["preview_places"].append(row.name)
        city_entry["places"].append(place_payload)

    for city_entry in city_map.values():
        city_entry["preview_places"] = city_entry["preview_places"][:3]
        city_entry["highlights"] = _build_city_highlights(city_entry)

    for place_payload in unassigned_places:
        scored = []
        for city_entry in city_map.values():
            suggestion_score = _suggest_place_for_city(city_entry, place_payload)
            if suggestion_score > 0:
                scored.append((suggestion_score, city_entry))

        scored.sort(key=lambda item: item[0], reverse=True)
        for suggestion_score, city_entry in scored[:3]:
            city_entry["suggested_unassigned_places"].append(
                {
                    "saved_place_id": place_payload["saved_place_id"],
                    "place_id": place_payload["place_id"],
                    "name": place_payload["name"],
                    "place_type": place_payload["place_type"],
                    "status": place_payload["status"],
                    "notes": place_payload["notes"],
                    "lat": place_payload["lat"],
                    "lon": place_payload["lon"],
                    "suggestion_score": suggestion_score,
                }
            )

    coverage_counts = {
        "ready": 0,
        "usable": 0,
        "thin": 0,
        "missing": 0,
        "needs_import": 0,
        "queued_imports": 0,
        "running_imports": 0,
        "route_readiness": "needs_imports",
    }

    for city_entry in city_map.values():
        unique_suggestions = {}
        for item in city_entry["suggested_unassigned_places"]:
            unique_suggestions[item["saved_place_id"]] = item
        city_entry["suggested_unassigned_places"] = list(unique_suggestions.values())[:3]
        city_entry["discovery_candidates"] = await _load_city_discovery_candidates(
            db, city_entry, saved_place_ids
        )
        city_entry["coverage"] = await _load_city_coverage(db, city_entry)
        coverage_counts[city_entry["coverage"]["level"]] += 1
        if city_entry["coverage"]["needs_import"]:
            coverage_counts["needs_import"] += 1
        if city_entry["coverage"]["active_import_status"] == "queued":
            coverage_counts["queued_imports"] += 1
        elif city_entry["coverage"]["active_import_status"] == "running":
            coverage_counts["running_imports"] += 1

    if coverage_counts["missing"] == 0 and coverage_counts["thin"] == 0:
        coverage_counts["route_readiness"] = "ready"
    elif coverage_counts["running_imports"] or coverage_counts["queued_imports"]:
        coverage_counts["route_readiness"] = "importing"
    elif coverage_counts["usable"] or coverage_counts["ready"]:
        coverage_counts["route_readiness"] = "partial"

    route_distance_km = None
    route_coordinates = [
        (row.lat, row.lon)
        for row in city_rows
        if row.lat is not None and row.lon is not None
    ]
    if len(route_coordinates) >= 2:
        route_distance_km = 0.0
        for index in range(1, len(route_coordinates)):
            leg_distance = _distance_km(
                route_coordinates[index - 1][0],
                route_coordinates[index - 1][1],
                route_coordinates[index][0],
                route_coordinates[index][1],
            )
            if leg_distance is not None:
                route_distance_km += leg_distance

    cities_without_places = sum(
        1 for city_entry in city_map.values() if city_entry["saved_count"] == 0
    )
    city_names = [row.name for row in city_rows]

    return {
        "trip_id": str(trip.id),
        "trip_name": trip.name,
        "participant_count": participant_count,
        "city_count": len(city_rows),
        "total_saved_places": total_saved_places,
        "assigned_saved_places": assigned_saved_places,
        "unassigned_saved_places": unassigned_saved_places,
        "route_label": _build_route_label(city_names),
        "route_distance_km": round(route_distance_km, 1)
        if route_distance_km is not None
        else None,
        "cities_without_places": cities_without_places,
        "route_highlights": _build_route_highlights(
            city_count=len(city_rows),
            participant_count=participant_count,
            route_distance_km=route_distance_km,
            assigned_saved_places=assigned_saved_places,
            unassigned_saved_places=unassigned_saved_places,
            cities_without_places=cities_without_places,
            top_place_types=assigned_place_type_totals,
        ),
        "coverage_summary": coverage_counts,
        "cities": [city_map[row.id] for row in city_rows],
        "unassigned_places": unassigned_places,
    }


@router.patch("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: str,
    payload: TripUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    trip_uuid = _parse_uuid(trip_id, "trip_id")
    trip = await db.get(Trip, trip_uuid)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    if payload.name is not None:
        trip.name = payload.name
    if payload.start_date is not None:
        trip.start_date = payload.start_date
    if payload.end_date is not None:
        trip.end_date = payload.end_date
    if payload.notes is not None:
        trip.notes = payload.notes

    await db.commit()
    return TripResponse(**await _load_trip_payload(db, trip_uuid))


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(trip_id: str, db: AsyncSession = Depends(get_db)):
    trip_uuid = _parse_uuid(trip_id, "trip_id")
    trip = await db.get(Trip, trip_uuid)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    await db.delete(trip)
    await db.commit()


@router.post(
    "/{trip_id}/cities",
    response_model=TripResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_city_to_trip(
    trip_id: str,
    payload: TripCityCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    trip_uuid = _parse_uuid(trip_id, "trip_id")
    if await db.get(Trip, trip_uuid) is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    location = None
    if payload.lat is not None and payload.lon is not None:
        location = WKTElement(f"POINT({payload.lon} {payload.lat})", srid=4326)

    next_sort_order = (
        await db.scalar(
            select(func.coalesce(func.max(City.sort_order), -1) + 1).where(
                City.trip_id == trip_uuid
            )
        )
        or 0
    )

    city = City(
        trip_id=trip_uuid,
        name=payload.name,
        country=payload.country,
        location=location,
        sort_order=next_sort_order,
        notes=payload.notes,
    )
    db.add(city)
    await db.commit()
    return TripResponse(**await _load_trip_payload(db, trip_uuid))


@router.patch("/{trip_id}/cities/{city_id}", response_model=TripResponse)
async def update_trip_city(
    trip_id: str,
    city_id: str,
    payload: TripCityUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    trip_uuid = _parse_uuid(trip_id, "trip_id")
    city_uuid = _parse_uuid(city_id, "city_id")
    city = await db.get(City, city_uuid)
    if city is None or city.trip_id != trip_uuid:
        raise HTTPException(status_code=404, detail="City not found")

    if payload.name is not None:
        city.name = payload.name
    if payload.country is not None:
        city.country = payload.country
    if payload.notes is not None:
        city.notes = payload.notes
    if payload.lat is not None and payload.lon is not None:
        city.location = WKTElement(f"POINT({payload.lon} {payload.lat})", srid=4326)

    await db.commit()
    return TripResponse(**await _load_trip_payload(db, trip_uuid))


@router.delete("/{trip_id}/cities/{city_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_city_from_trip(
    trip_id: str,
    city_id: str,
    db: AsyncSession = Depends(get_db),
):
    trip_uuid = _parse_uuid(trip_id, "trip_id")
    city_uuid = _parse_uuid(city_id, "city_id")
    city = await db.get(City, city_uuid)
    if city is None or city.trip_id != trip_uuid:
        raise HTTPException(status_code=404, detail="City not found")
    await db.delete(city)
    await db.commit()

    remaining = (
        await db.execute(
            select(City)
            .where(City.trip_id == trip_uuid)
            .order_by(City.sort_order.asc(), City.created_at.asc(), City.name.asc())
        )
    ).scalars().all()
    for index, remaining_city in enumerate(remaining):
        remaining_city.sort_order = index
    await db.commit()


@router.post("/{trip_id}/cities/reorder", response_model=TripResponse)
async def reorder_trip_cities(
    trip_id: str,
    payload: TripCityReorderRequest,
    db: AsyncSession = Depends(get_db),
):
    trip_uuid = _parse_uuid(trip_id, "trip_id")
    trip = await db.get(Trip, trip_uuid)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    city_ids = [_parse_uuid(city_id, "city_id") for city_id in payload.city_ids]
    cities = (
        await db.execute(select(City).where(City.trip_id == trip_uuid))
    ).scalars().all()
    existing_ids = {city.id for city in cities}
    if set(city_ids) != existing_ids or len(city_ids) != len(existing_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="city_ids must contain each trip city exactly once",
        )

    city_by_id = {city.id: city for city in cities}
    for index, city_uuid in enumerate(city_ids):
        city_by_id[city_uuid].sort_order = index

    await db.commit()
    return TripResponse(**await _load_trip_payload(db, trip_uuid))


@router.post(
    "/{trip_id}/participants",
    response_model=TripResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_trip_participant(
    trip_id: str,
    payload: TripParticipantCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    trip_uuid = _parse_uuid(trip_id, "trip_id")
    if await db.get(Trip, trip_uuid) is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    participant = TripParticipant(
        trip_id=trip_uuid,
        name=payload.name,
        note=payload.note,
    )
    db.add(participant)
    await db.commit()
    return TripResponse(**await _load_trip_payload(db, trip_uuid))


@router.delete(
    "/{trip_id}/participants/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_trip_participant(
    trip_id: str,
    participant_id: str,
    db: AsyncSession = Depends(get_db),
):
    trip_uuid = _parse_uuid(trip_id, "trip_id")
    participant_uuid = _parse_uuid(participant_id, "participant_id")
    participant = await db.get(TripParticipant, participant_uuid)
    if participant is None or participant.trip_id != trip_uuid:
        raise HTTPException(status_code=404, detail="Participant not found")

    payer_refs = await db.scalar(
        select(func.count()).select_from(Expense).where(
            Expense.paid_by_participant_id == participant_uuid
        )
    )
    share_refs = await db.scalar(
        select(func.count()).select_from(ExpenseSplit).where(
            ExpenseSplit.participant_id == participant_uuid
        )
    )
    if (payer_refs or 0) > 0 or (share_refs or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Participant is already referenced by expenses",
        )

    await db.delete(participant)
    await db.commit()


@router.get("/{trip_id}/overview", response_model=TripOverviewResponse)
async def get_trip_overview(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
):
    trip_uuid = _parse_uuid(trip_id, "trip_id")
    return TripOverviewResponse(**await _load_trip_overview_payload(db, trip_uuid))


@router.post("/{trip_id}/coverage/imports", response_model=TripCoverageImportResponse)
async def queue_trip_coverage_imports(
    trip_id: str,
    payload: TripCoverageImportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    trip_uuid = _parse_uuid(trip_id, "trip_id")
    trip = await db.get(Trip, trip_uuid)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    city_rows = (
        await db.execute(
            select(
                City.id,
                City.name,
                City.country,
                func.ST_Y(City.location).label("lat"),
                func.ST_X(City.location).label("lon"),
                City.sort_order,
            )
            .where(City.trip_id == trip_uuid)
            .order_by(City.sort_order.asc(), City.created_at.asc(), City.name.asc())
        )
    ).all()

    if not city_rows:
        return TripCoverageImportResponse(
            data=[],
            queued_count=0,
            reused_count=0,
            message="Trip has no cities yet",
        )

    selected_ids = {_parse_uuid(city_id, "city_id") for city_id in payload.city_ids}
    cities_to_queue: list[tuple[str, str | None]] = []

    for row in city_rows:
        if selected_ids and row.id not in selected_ids:
            continue

        coverage = await _load_city_coverage(
            db,
            {
                "name": row.name,
                "country": row.country,
                "lat": float(row.lat) if row.lat is not None else None,
                "lon": float(row.lon) if row.lon is not None else None,
            },
        )
        if selected_ids or coverage["needs_import"]:
            cities_to_queue.append((row.name, row.country))

    if not cities_to_queue:
        return TripCoverageImportResponse(
            data=[],
            queued_count=0,
            reused_count=0,
            message="All trip cities already have usable local coverage",
        )

    jobs, queued_count = await enqueue_import_jobs(db, background_tasks, cities_to_queue)
    data = [
        {
            "id": str(job.id),
            "city": job.city,
            "country": job.country,
            "region": job.region,
            "status": job.status,
            "imported_count": int(job.imported_count or 0),
            "total_elements": int(job.total_elements or 0),
            "error": job.error,
            "created_at": job.created_at,
            "finished_at": job.finished_at,
        }
        for job in jobs
    ]
    reused_count = len(jobs) - queued_count
    return TripCoverageImportResponse(
        data=data,
        queued_count=queued_count,
        reused_count=reused_count,
        message="Trip coverage imports queued"
        if queued_count
        else "Existing import jobs already cover the requested trip cities",
    )
