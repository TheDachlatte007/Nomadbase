"""Overpass API importer — fetches POIs from OpenStreetMap for a given city."""

from __future__ import annotations

import logging
from uuid import uuid4

import httpx
from geoalchemy2 import WKTElement
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.place import Place

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Maps (OSM key, OSM value) → our place_type
TAG_TYPE_MAP: dict[tuple[str, str], str] = {
    ("amenity", "restaurant"): "restaurant",
    ("amenity", "fast_food"): "restaurant",
    ("amenity", "food_court"): "restaurant",
    ("amenity", "cafe"): "cafe",
    ("amenity", "bar"): "cafe",
    ("amenity", "pub"): "cafe",
    ("amenity", "ice_cream"): "cafe",
    ("amenity", "bakery"): "cafe",
    ("tourism", "attraction"): "attraction",
    ("tourism", "museum"): "cultural",
    ("tourism", "gallery"): "cultural",
    ("tourism", "zoo"): "attraction",
    ("tourism", "theme_park"): "attraction",
    ("tourism", "aquarium"): "attraction",
    ("tourism", "viewpoint"): "viewpoint",
    ("leisure", "park"): "park",
    ("leisure", "garden"): "park",
    ("leisure", "nature_reserve"): "park",
    ("natural", "peak"): "hiking",
    ("natural", "waterfall"): "hiking",
    ("natural", "beach"): "park",
    ("natural", "cave_entrance"): "hiking",
}

# Overpass union filter lines — only named POIs (unnamed ones are discarded anyway)
_FILTERS = [
    f'nwr["{k}"="{v}"]["name"]'
    for k, v in TAG_TYPE_MAP
]


def _overpass_query(south: float, west: float, north: float, east: float) -> str:
    bbox = f"{south},{west},{north},{east}"
    filters = "\n  ".join(f"{f}({bbox});" for f in _FILTERS)
    return f"""
[out:json][timeout:90][maxsize:104857600];
(
  {filters}
);
out center tags;
"""


def _detect_type(tags: dict) -> str:
    for key in ("amenity", "tourism", "leisure", "natural"):
        value = tags.get(key)
        if value and (key, value) in TAG_TYPE_MAP:
            return TAG_TYPE_MAP[(key, value)]
    return "attraction"


def _build_place(element: dict, region: str) -> dict | None:
    tags = element.get("tags", {})
    name = tags.get("name") or tags.get("name:en")
    if not name:
        return None

    # Get coordinates — nodes have lat/lon directly, ways/relations have center
    if element["type"] == "node":
        lat = element.get("lat")
        lon = element.get("lon")
    else:
        center = element.get("center", {})
        lat = center.get("lat")
        lon = center.get("lon")

    if lat is None or lon is None:
        return None

    osm_id = element.get("id")
    place_type = _detect_type(tags)

    # Build a short description from common OSM tags
    description_parts = []
    if tags.get("description"):
        description_parts.append(tags["description"])
    elif tags.get("wikipedia"):
        description_parts.append(f"Wikipedia: {tags['wikipedia']}")
    elif tags.get("tourism") == "viewpoint":
        description_parts.append("Scenic viewpoint")
    elif tags.get("natural") == "peak" and tags.get("ele"):
        description_parts.append(f"Summit at {tags['ele']} m")

    clean_tags = {
        k: v
        for k, v in tags.items()
        if k
        not in (
            "name",
            "name:en",
            "description",
            "source",
            "wikipedia",
            "wikidata",
        )
        and not k.startswith("name:")
    }

    return {
        "id": uuid4(),
        "osm_id": osm_id,
        "name": name[:500],
        "place_type": place_type,
        "location": WKTElement(f"POINT({lon} {lat})", srid=4326),
        "tags": clean_tags,
        "description": description_parts[0] if description_parts else None,
        "source": "osm",
        "raw_osm_tags": tags,
        "region": region,
    }


async def geocode_city(city: str, country: str | None = None) -> dict | None:
    """Returns bbox dict with south/west/north/east, or None if not found."""
    query = f"{city}, {country}" if country else city
    async with httpx.AsyncClient(
        headers={"User-Agent": "NomadBase/0.1 (personal travel app)"},
        timeout=15,
    ) as client:
        resp = await client.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1},
        )
        resp.raise_for_status()
        results = resp.json()

    if not results:
        return None

    bb = results[0].get("boundingbox")  # [south, north, west, east]
    if not bb or len(bb) < 4:
        return None

    return {
        "south": float(bb[0]),
        "north": float(bb[1]),
        "west": float(bb[2]),
        "east": float(bb[3]),
        "display_name": results[0].get("display_name", city),
    }


async def fetch_overpass(bbox: dict) -> list[dict]:
    """Queries Overpass and returns raw elements."""
    query = _overpass_query(bbox["south"], bbox["west"], bbox["north"], bbox["east"])
    async with httpx.AsyncClient(timeout=150) as client:
        resp = await client.post(OVERPASS_URL, data={"data": query})
        resp.raise_for_status()
        return resp.json().get("elements", [])


async def import_city(
    city: str, country: str | None, db: AsyncSession
) -> dict:
    """
    Full import pipeline: geocode → Overpass fetch → upsert into DB.
    Returns a summary dict.
    """
    logger.info("Importing %s, %s", city, country)

    bbox = await geocode_city(city, country)
    if bbox is None:
        raise ValueError(f"Could not geocode city: {city}")

    region = city if not country else f"{city}, {country}"
    elements = await fetch_overpass(bbox)
    logger.info("Overpass returned %d elements for %s", len(elements), region)

    places = []
    seen_osm_ids: set[int] = set()

    for el in elements:
        place = _build_place(el, region)
        if place is None:
            continue
        osm_id = place["osm_id"]
        if osm_id in seen_osm_ids:
            continue
        seen_osm_ids.add(osm_id)
        places.append(place)

    if not places:
        return {"region": region, "imported": 0, "skipped": len(elements)}

    # Upsert on osm_id — skip if osm_id already exists
    inserted = 0
    for place in places:
        stmt = pg_insert(Place).values(
            id=place["id"],
            osm_id=place["osm_id"],
            name=place["name"],
            place_type=place["place_type"],
            location=place["location"],
            tags=place["tags"],
            description=place["description"],
            source=place["source"],
            raw_osm_tags=place["raw_osm_tags"],
            region=place["region"],
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["osm_id"],
            set_={
                "name": stmt.excluded.name,
                "place_type": stmt.excluded.place_type,
                "location": stmt.excluded.location,
                "tags": stmt.excluded.tags,
                "description": stmt.excluded.description,
                "raw_osm_tags": stmt.excluded.raw_osm_tags,
                "region": stmt.excluded.region,
            },
        )
        await db.execute(stmt)
        inserted += 1

    await db.commit()

    logger.info("Upserted %d places for %s", inserted, region)
    return {
        "region": region,
        "imported": inserted,
        "total_elements": len(elements),
        "bbox": bbox,
    }
