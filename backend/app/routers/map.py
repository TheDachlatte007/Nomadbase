import json
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Text, and_, case, cast, func, or_, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.city import City
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
        Place.raw_osm_tags,
        func.ST_Y(Place.location).label("lat"),
        func.ST_X(Place.location).label("lon"),
    )


def _parse_uuid(value: str, field_name: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} must be a valid UUID",
        ) from exc


def _parse_wikipedia_url(raw_tags: dict | None) -> str | None:
    wikipedia = (raw_tags or {}).get("wikipedia")
    if not wikipedia:
        return None
    if wikipedia.startswith("http://") or wikipedia.startswith("https://"):
        return wikipedia
    if ":" not in wikipedia:
        return None
    language, article = wikipedia.split(":", 1)
    if not language or not article:
        return None
    return f"https://{language}.wikipedia.org/wiki/{quote(article.replace(' ', '_'))}"


def _build_address(raw_tags: dict | None) -> str | None:
    if not raw_tags:
        return None
    street = raw_tags.get("addr:street")
    house_number = raw_tags.get("addr:housenumber")
    suburb = raw_tags.get("addr:suburb")
    parts = []
    if street:
        if house_number:
            parts.append(f"{street} {house_number}")
        else:
            parts.append(street)
    if suburb:
        parts.append(suburb)
    return ", ".join(parts) if parts else None


def _build_context_line(
    place_type: str, tags: dict | None, raw_tags: dict | None, address: str | None
) -> str | None:
    tags = tags or {}
    raw_tags = raw_tags or {}
    cuisine = tags.get("cuisine")
    brand = raw_tags.get("brand")
    tourism = raw_tags.get("tourism")

    parts = []
    if cuisine:
        parts.append(cuisine.replace(";", " · ").replace("_", " "))
    elif brand:
        parts.append(brand)
    elif tourism and tourism != place_type:
        parts.append(tourism.replace("_", " "))

    if address:
        parts.append(address)

    return " · ".join(parts[:2]) if parts else None


def _fallback_description(
    description: str | None,
    place_type: str,
    tags: dict | None,
    raw_tags: dict | None,
    context_line: str | None,
) -> str | None:
    if description:
        return description
    tags = tags or {}
    raw_tags = raw_tags or {}
    if tags.get("cuisine"):
        return f"Cuisine: {tags['cuisine'].replace(';', ', ').replace('_', ' ')}"
    if raw_tags.get("description"):
        return raw_tags["description"]
    if raw_tags.get("opening_hours"):
        return f"Opening hours: {raw_tags['opening_hours']}"
    if context_line:
        return context_line
    return f"{place_type.replace('_', ' ').title()} imported from OpenStreetMap"


def _serialize_place(row) -> dict:
    raw_tags = row.raw_osm_tags or {}
    address = _build_address(raw_tags)
    context_line = _build_context_line(row.place_type, row.tags or {}, raw_tags, address)
    return {
        "id": str(row.id),
        "name": row.name,
        "place_type": row.place_type,
        "description": _fallback_description(
            row.description, row.place_type, row.tags or {}, raw_tags, context_line
        ),
        "region": row.region,
        "source": row.source,
        "tags": row.tags or {},
        "address": address,
        "cuisine": (row.tags or {}).get("cuisine"),
        "context_line": context_line,
        "website_url": raw_tags.get("website")
        or raw_tags.get("contact:website")
        or raw_tags.get("url"),
        "wikipedia_url": _parse_wikipedia_url(raw_tags),
        "wikidata_id": raw_tags.get("wikidata"),
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
    trip_id: str | None = None,
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
        filters.append(Place.region.ilike(f"%{region.strip()}%"))
    if trip_id:
        trip_uuid = _parse_uuid(trip_id, "trip_id")
        trip_city_rows = (
            await db.execute(
                select(City.name, City.country).where(City.trip_id == trip_uuid)
            )
        ).all()
        city_filters = []
        for row in trip_city_rows:
            if row.name:
                city_filters.append(Place.region.ilike(f"%{row.name.strip()}%"))
            if row.name and row.country:
                city_filters.append(
                    Place.region.ilike(f"%{row.name.strip()}%{row.country.strip()}%")
                )
        if city_filters:
            filters.append(or_(*city_filters))
    if q:
        pattern = f"%{q.strip()}%"
        filters.append(
            or_(
                Place.name.ilike(pattern),
                Place.description.ilike(pattern),
                Place.region.ilike(pattern),
                cast(Place.tags, Text).ilike(pattern),
                cast(Place.raw_osm_tags, Text).ilike(pattern),
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

    if q:
        normalized_q = q.strip().lower()
        order_clause = [
            case(
                (func.lower(Place.name) == normalized_q, 0),
                (Place.name.ilike(f"{q.strip()}%"), 1),
                else_=2,
            ),
            Place.name.asc(),
        ]
    else:
        order_clause = [Place.name.asc()]

    stmt = _base_place_select().order_by(*order_clause).limit(limit).offset(offset)
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
    message = "Nearby places" if data else "No nearby places found"

    return PlaceListResponse(data=data, total=len(data), total_available=len(data), message=message)
