from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from geoalchemy2 import WKTElement
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.city import City
from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.models.trip import Trip
from app.models.trip_participant import TripParticipant
from app.schemas.trip import (
    TripCityCreateRequest,
    TripCreateRequest,
    TripListResponse,
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
            )
            .where(City.trip_id.in_(ordered_trip_ids))
            .order_by(City.created_at.asc(), City.name.asc())
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

    city = City(
        trip_id=trip_uuid,
        name=payload.name,
        country=payload.country,
        location=location,
    )
    db.add(city)
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
