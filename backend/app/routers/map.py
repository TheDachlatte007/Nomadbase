from fastapi import APIRouter, Depends, Query
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.place import Place
from app.schemas.place import PlaceListResponse

router = APIRouter()


@router.get("/")
async def map_root():
    return {
        "message": "Map endpoints",
        "endpoints": ["/places", "/places/nearby"],
    }


def _base_place_select() -> Select:
    return select(
        Place.id,
        Place.name,
        Place.place_type,
        Place.description,
        Place.region,
        Place.source,
        Place.tags,
        func.ST_Y(Place.location).label("lat"),
        func.ST_X(Place.location).label("lon"),
    )


def _serialize_place(row) -> dict:
    return {
        "id": str(row.id),
        "name": row.name,
        "place_type": row.place_type,
        "description": row.description,
        "region": row.region,
        "source": row.source,
        "tags": row.tags or {},
        "lat": float(row.lat),
        "lon": float(row.lon),
    }


@router.get("/places", response_model=PlaceListResponse)
async def list_places(
    place_type: str | None = None,
    region: str | None = None,
    q: str | None = None,
    limit: int = Query(default=24, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = _base_place_select().order_by(Place.name.asc()).limit(limit)

    if place_type:
        stmt = stmt.where(Place.place_type == place_type)

    if region:
        stmt = stmt.where(Place.region == region)

    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Place.name.ilike(pattern),
                Place.description.ilike(pattern),
                Place.region.ilike(pattern),
            )
        )

    result = await db.execute(stmt)
    rows = result.all()
    data = [_serialize_place(row) for row in rows]
    message = "Live alpha places" if data else "No places found for current filters"

    return PlaceListResponse(data=data, total=len(data), message=message)


@router.get("/places/nearby", response_model=PlaceListResponse)
async def nearby_places(
    lat: float,
    lon: float,
    radius_m: int = Query(default=2500, ge=100, le=25000),
    limit: int = Query(default=12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    stmt = (
        _base_place_select()
        .where(func.ST_DistanceSphere(Place.location, point) <= radius_m)
        .order_by(func.ST_DistanceSphere(Place.location, point).asc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()
    data = [_serialize_place(row) for row in rows]
    message = "Nearby alpha places" if data else "No nearby places found"

    return PlaceListResponse(data=data, total=len(data), message=message)
