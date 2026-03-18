from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from geoalchemy2 import WKTElement
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.city import City
from app.models.trip import Trip
from app.schemas.trip import (
    TripCityCreateRequest,
    TripCreateRequest,
    TripListResponse,
    TripResponse,
    TripUpdateRequest,
)

router = APIRouter()


def _serialize_trip(rows) -> list[dict]:
    trips: dict[str, dict] = {}

    for row in rows:
        trip_id = str(row.trip_id)
        trip = trips.setdefault(
            trip_id,
            {
                "id": trip_id,
                "name": row.trip_name,
                "start_date": row.start_date,
                "end_date": row.end_date,
                "notes": row.notes,
                "created_at": row.trip_created_at,
                "updated_at": row.trip_updated_at,
                "cities": [],
            },
        )

        if row.city_id is not None:
            trip["cities"].append(
                {
                    "id": str(row.city_id),
                    "name": row.city_name,
                    "country": row.country,
                    "lat": float(row.lat) if row.lat is not None else None,
                    "lon": float(row.lon) if row.lon is not None else None,
                    "created_at": row.city_created_at,
                    "updated_at": row.city_updated_at,
                }
            )

    return list(trips.values())


def _trip_stmt():
    return (
        select(
            Trip.id.label("trip_id"),
            Trip.name.label("trip_name"),
            Trip.start_date,
            Trip.end_date,
            Trip.notes,
            Trip.created_at.label("trip_created_at"),
            Trip.updated_at.label("trip_updated_at"),
            City.id.label("city_id"),
            City.name.label("city_name"),
            City.country,
            func.ST_Y(City.location).label("lat"),
            func.ST_X(City.location).label("lon"),
            City.created_at.label("city_created_at"),
            City.updated_at.label("city_updated_at"),
        )
        .outerjoin(City, City.trip_id == Trip.id)
        .order_by(Trip.created_at.desc(), City.created_at.asc())
    )


@router.get("/", response_model=TripListResponse)
async def list_trips(db: AsyncSession = Depends(get_db)):
    result = await db.execute(_trip_stmt())
    data = _serialize_trip(result.all())
    return TripListResponse(
        data=data,
        total=len(data),
        message="Trips" if data else "No trips yet",
    )


@router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    payload: TripCreateRequest, db: AsyncSession = Depends(get_db)
):
    trip = Trip(
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        notes=payload.notes,
    )
    db.add(trip)
    await db.commit()
    await db.refresh(trip)

    result = await db.execute(_trip_stmt().where(Trip.id == trip.id))
    data = _serialize_trip(result.all())[0]
    return TripResponse(**data)


def _parse_trip_uuid(trip_id: str) -> "UUID":
    try:
        return UUID(trip_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="trip_id must be a valid UUID",
        ) from exc


@router.patch("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: str,
    payload: TripUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    trip_uuid = _parse_trip_uuid(trip_id)
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

    result = await db.execute(_trip_stmt().where(Trip.id == trip_uuid))
    data = _serialize_trip(result.all())[0]
    return TripResponse(**data)


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(trip_id: str, db: AsyncSession = Depends(get_db)):
    trip_uuid = _parse_trip_uuid(trip_id)
    trip = await db.get(Trip, trip_uuid)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    await db.delete(trip)
    await db.commit()


@router.delete(
    "/{trip_id}/cities/{city_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_city_from_trip(
    trip_id: str,
    city_id: str,
    db: AsyncSession = Depends(get_db),
):
    trip_uuid = _parse_trip_uuid(trip_id)
    try:
        city_uuid = UUID(city_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="city_id must be a valid UUID",
        ) from exc

    city = await db.get(City, city_uuid)
    if city is None or city.trip_id != trip_uuid:
        raise HTTPException(status_code=404, detail="City not found")
    await db.delete(city)
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
    trip_uuid = _parse_trip_uuid(trip_id)
    trip = await db.get(Trip, trip_uuid)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    location = None
    if payload.lat is not None and payload.lon is not None:
        location = WKTElement(f"POINT({payload.lon} {payload.lat})", srid=4326)

    city = City(
        trip_id=trip_uuid,
        name=payload.name,
        country=payload.country,
        location=location,
    )
    db.add(city)
    await db.commit()

    result = await db.execute(_trip_stmt().where(Trip.id == trip_uuid))
    data = _serialize_trip(result.all())[0]
    return TripResponse(**data)
