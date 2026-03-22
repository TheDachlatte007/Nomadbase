from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.city import City
from app.models.place import Place
from app.models.saved_place import SavedPlace
from app.models.trip import Trip
from app.schemas.save import (
    SavePlaceRequest,
    SavedPlaceListResponse,
    SavedPlaceResponse,
    UpdateSavedPlaceRequest,
)

router = APIRouter()


def _saved_place_select():
    return select(
        SavedPlace.id.label("saved_id"),
        SavedPlace.place_id,
        SavedPlace.trip_id,
        SavedPlace.status,
        SavedPlace.notes,
        SavedPlace.created_at,
        SavedPlace.updated_at,
        Place.id.label("place_uuid"),
        Place.name,
        Place.place_type,
        Place.description,
        Place.region,
        Place.source,
        Place.tags,
        Trip.name.label("trip_name"),
        City.id.label("city_uuid"),
        City.name.label("city_name"),
        func.ST_Y(Place.location).label("lat"),
        func.ST_X(Place.location).label("lon"),
    ).join(Place, Place.id == SavedPlace.place_id).outerjoin(Trip, Trip.id == SavedPlace.trip_id).outerjoin(City, City.id == SavedPlace.city_id)


def _serialize_saved_place(row) -> dict:
    return {
        "id": str(row.saved_id),
        "place_id": str(row.place_id),
        "trip_id": str(row.trip_id) if row.trip_id else None,
        "trip_name": row.trip_name,
        "city_id": str(row.city_uuid) if row.city_uuid else None,
        "city_name": row.city_name,
        "status": row.status,
        "notes": row.notes,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "place": {
            "id": str(row.place_uuid),
            "name": row.name,
            "place_type": row.place_type,
            "description": row.description,
            "region": row.region,
            "source": row.source,
            "tags": row.tags or {},
            "lat": float(row.lat),
            "lon": float(row.lon),
        },
    }


def _parse_uuid(value: str, field_name: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} must be a valid UUID",
        ) from exc


async def _require_trip(db: AsyncSession, trip_id: UUID) -> Trip:
    trip = await db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


async def _require_city_for_trip(
    db: AsyncSession, city_id: UUID, trip_id: UUID
) -> City:
    city = await db.get(City, city_id)
    if city is None or city.trip_id != trip_id:
        raise HTTPException(status_code=404, detail="City not found for this trip")
    return city


async def _ensure_unique_scope(
    db: AsyncSession,
    place_id: UUID,
    trip_id: UUID | None,
    ignore_saved_id: UUID | None = None,
) -> None:
    stmt = select(SavedPlace).where(
        SavedPlace.place_id == place_id,
        SavedPlace.trip_id == trip_id,
    )
    if ignore_saved_id:
        stmt = stmt.where(SavedPlace.id != ignore_saved_id)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="This place is already saved for that scope",
        )


@router.get("/", response_model=SavedPlaceListResponse)
async def list_saved_places(
    trip_id: str | None = Query(default=None),
    include_global: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
):
    stmt = _saved_place_select().order_by(SavedPlace.created_at.desc())
    if trip_id:
        trip_uuid = _parse_uuid(trip_id, "trip_id")
        if include_global:
            stmt = stmt.where(
                or_(SavedPlace.trip_id == trip_uuid, SavedPlace.trip_id.is_(None))
            )
        else:
            stmt = stmt.where(SavedPlace.trip_id == trip_uuid)
    result = await db.execute(stmt)
    rows = result.all()
    data = [_serialize_saved_place(row) for row in rows]
    return SavedPlaceListResponse(
        data=data,
        total=len(data),
        message="Saved places" if data else "No saved places yet",
    )


@router.post("/", response_model=SavedPlaceResponse)
async def save_place(
    payload: SavePlaceRequest, db: AsyncSession = Depends(get_db)
):
    place_uuid = _parse_uuid(payload.place_id, "place_id")
    trip_uuid = _parse_uuid(payload.trip_id, "trip_id") if payload.trip_id else None
    city_uuid = _parse_uuid(payload.city_id, "city_id") if payload.city_id else None

    place = await db.get(Place, place_uuid)
    if place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    if trip_uuid:
        await _require_trip(db, trip_uuid)
    if city_uuid:
        if trip_uuid is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="city_id requires a trip-scoped save",
            )
        await _require_city_for_trip(db, city_uuid, trip_uuid)

    existing = await db.execute(
        select(SavedPlace).where(
            SavedPlace.place_id == place_uuid,
            SavedPlace.trip_id == trip_uuid,
        )
    )
    saved_place = existing.scalar_one_or_none()

    if saved_place is None:
        await _ensure_unique_scope(db, place_uuid, trip_uuid)
        saved_place = SavedPlace(
            place_id=place_uuid,
            trip_id=trip_uuid,
            city_id=city_uuid,
            status=payload.status,
            notes=payload.notes,
        )
        db.add(saved_place)
    else:
        saved_place.trip_id = trip_uuid
        saved_place.city_id = city_uuid
        saved_place.status = payload.status
        saved_place.notes = payload.notes

    await db.commit()

    result = await db.execute(
        _saved_place_select().where(SavedPlace.id == saved_place.id)
    )
    row = result.one()
    return SavedPlaceResponse(**_serialize_saved_place(row))


@router.patch("/{saved_place_id}", response_model=SavedPlaceResponse)
async def update_saved_place(
    saved_place_id: str,
    payload: UpdateSavedPlaceRequest,
    db: AsyncSession = Depends(get_db),
):
    saved_uuid = _parse_uuid(saved_place_id, "saved_place_id")

    saved_place = await db.get(SavedPlace, saved_uuid)
    if saved_place is None:
        raise HTTPException(status_code=404, detail="Saved place not found")

    trip_id_in_payload = "trip_id" in payload.model_fields_set
    city_id_in_payload = "city_id" in payload.model_fields_set

    if trip_id_in_payload:
        trip_uuid = _parse_uuid(payload.trip_id, "trip_id") if payload.trip_id else None
        if trip_uuid:
            await _require_trip(db, trip_uuid)
        await _ensure_unique_scope(
            db,
            saved_place.place_id,
            trip_uuid,
            ignore_saved_id=saved_place.id,
        )
        saved_place.trip_id = trip_uuid
        if not city_id_in_payload:
            saved_place.city_id = None
    else:
        trip_uuid = saved_place.trip_id

    if city_id_in_payload:
        city_uuid = _parse_uuid(payload.city_id, "city_id") if payload.city_id else None
        if city_uuid is not None:
            if trip_uuid is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="city_id requires a trip-scoped save",
                )
            await _require_city_for_trip(db, city_uuid, trip_uuid)
        saved_place.city_id = city_uuid
    if payload.status is not None:
        saved_place.status = payload.status
    if payload.notes is not None:
        saved_place.notes = payload.notes

    await db.commit()

    result = await db.execute(
        _saved_place_select().where(SavedPlace.id == saved_uuid)
    )
    row = result.one()
    return SavedPlaceResponse(**_serialize_saved_place(row))


@router.delete("/{saved_place_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_place(
    saved_place_id: str,
    db: AsyncSession = Depends(get_db),
):
    saved_uuid = _parse_uuid(saved_place_id, "saved_place_id")

    saved_place = await db.get(SavedPlace, saved_uuid)
    if saved_place is None:
        raise HTTPException(status_code=404, detail="Saved place not found")

    await db.delete(saved_place)
    await db.commit()
