import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from geoalchemy2 import WKTElement
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.city import City
from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.models.place import Place
from app.models.saved_place import SavedPlace
from app.models.trip import Trip
from app.models.trip_participant import TripParticipant
from app.schemas.trip import (
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

router = APIRouter()


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

    for row in saved_rows:
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

    for city_entry in city_map.values():
        unique_suggestions = {}
        for item in city_entry["suggested_unassigned_places"]:
            unique_suggestions[item["saved_place_id"]] = item
        city_entry["suggested_unassigned_places"] = list(unique_suggestions.values())[:3]

    return {
        "trip_id": str(trip.id),
        "trip_name": trip.name,
        "participant_count": participant_count,
        "city_count": len(city_rows),
        "total_saved_places": total_saved_places,
        "assigned_saved_places": assigned_saved_places,
        "unassigned_saved_places": unassigned_saved_places,
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
