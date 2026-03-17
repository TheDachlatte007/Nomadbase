from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.place import Place
from app.models.saved_place import SavedPlace
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
        func.ST_Y(Place.location).label("lat"),
        func.ST_X(Place.location).label("lon"),
    ).join(Place, Place.id == SavedPlace.place_id)


def _serialize_saved_place(row) -> dict:
    return {
        "id": str(row.saved_id),
        "place_id": str(row.place_id),
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


@router.get("/", response_model=SavedPlaceListResponse)
async def list_saved_places(db: AsyncSession = Depends(get_db)):
    stmt = _saved_place_select().order_by(SavedPlace.created_at.desc())
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
    try:
        place_uuid = UUID(payload.place_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="place_id must be a valid UUID",
        ) from exc

    place = await db.get(Place, place_uuid)
    if place is None:
        raise HTTPException(status_code=404, detail="Place not found")

    existing = await db.execute(
        select(SavedPlace).where(SavedPlace.place_id == place_uuid)
    )
    saved_place = existing.scalar_one_or_none()

    if saved_place is None:
        saved_place = SavedPlace(
            place_id=place_uuid, status=payload.status, notes=payload.notes
        )
        db.add(saved_place)
    else:
        saved_place.status = payload.status
        saved_place.notes = payload.notes

    await db.commit()

    result = await db.execute(
        _saved_place_select().where(SavedPlace.place_id == place_uuid)
    )
    row = result.one()
    return SavedPlaceResponse(**_serialize_saved_place(row))


@router.patch("/{saved_place_id}", response_model=SavedPlaceResponse)
async def update_saved_place(
    saved_place_id: str,
    payload: UpdateSavedPlaceRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        saved_uuid = UUID(saved_place_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="saved_place_id must be a valid UUID",
        ) from exc

    saved_place = await db.get(SavedPlace, saved_uuid)
    if saved_place is None:
        raise HTTPException(status_code=404, detail="Saved place not found")

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
    try:
        saved_uuid = UUID(saved_place_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="saved_place_id must be a valid UUID",
        ) from exc

    saved_place = await db.get(SavedPlace, saved_uuid)
    if saved_place is None:
        raise HTTPException(status_code=404, detail="Saved place not found")

    await db.delete(saved_place)
    await db.commit()
