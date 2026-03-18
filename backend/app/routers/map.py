import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, cast, func, or_, select
from sqlalchemy.dialects.postgresql import JSONB
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


def _base_place_select():
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


# Allowed tag filters mapped to the JSONB key/value pair they assert
_ALLOWED_TAG_FILTERS: dict[str, dict[str, str]] = {
    "vegan": {"diet:vegan": "yes"},
    "vegetarian": {"diet:vegetarian": "yes"},
    "outdoor_seating": {"outdoor_seating": "yes"},
    "wifi": {"internet_access": "wlan"},
    "wheelchair": {"wheelchair": "yes"},
}


@router.get("/places", response_model=PlaceListResponse)
async def list_places(
    place_type: str | None = None,
    region: str | None = None,
    q: str | None = None,
    tag_filters: str | None = Query(default=None, description="Comma-separated tag keys, e.g. vegan,outdoor_seating"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if place_type:
        filters.append(Place.place_type == place_type)
    if region:
        filters.append(Place.region == region)
    if q:
        pattern = f"%{q.strip()}%"
        filters.append(
            or_(
                Place.name.ilike(pattern),
                Place.description.ilike(pattern),
                Place.region.ilike(pattern),
            )
        )
    if tag_filters:
        for key in tag_filters.split(","):
            key = key.strip()
            if key in _ALLOWED_TAG_FILTERS:
                required = _ALLOWED_TAG_FILTERS[key]
                filters.append(Place.tags.contains(cast(json.dumps(required), JSONB)))

    count_stmt = select(func.count()).select_from(Place)
    if filters:
        count_stmt = count_stmt.where(and_(*filters))
    total_available = (await db.execute(count_stmt)).scalar_one()

    stmt = _base_place_select().order_by(Place.name.asc()).limit(limit).offset(offset)
    if filters:
        stmt = stmt.where(and_(*filters))

    result = await db.execute(stmt)
    rows = result.all()
    data = [_serialize_place(row) for row in rows]
    message = "Live alpha places" if data else "No places found for current filters"

    return PlaceListResponse(data=data, total=len(data), total_available=total_available, message=message)


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
