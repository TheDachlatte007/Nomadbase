from uuid import uuid4

from geoalchemy2 import WKTElement
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db import async_session_maker
from app.models.place import Place
from app.sample_places import ALPHA_SAMPLE_PLACES


async def seed_alpha_places() -> int:
    payload = []
    for place in ALPHA_SAMPLE_PLACES:
        payload.append(
            {
                "id": uuid4(),
                "osm_id": place["osm_id"],
                "name": place["name"],
                "place_type": place["place_type"],
                "location": WKTElement(
                    f"POINT({place['lon']} {place['lat']})", srid=4326
                ),
                "tags": place["tags"],
                "description": place["description"],
                "source": "alpha_seed",
                "raw_osm_tags": {"alpha_seed": True},
                "region": place["region"],
            }
        )

    stmt = pg_insert(Place).values(payload)
    stmt = stmt.on_conflict_do_update(
        index_elements=["osm_id"],
        set_={
            "name": stmt.excluded.name,
            "place_type": stmt.excluded.place_type,
            "location": stmt.excluded.location,
            "tags": stmt.excluded.tags,
            "description": stmt.excluded.description,
            "source": stmt.excluded.source,
            "raw_osm_tags": stmt.excluded.raw_osm_tags,
            "region": stmt.excluded.region,
        },
    )

    async with async_session_maker() as session:
        await session.execute(stmt)
        await session.commit()

    return len(payload)


async def main() -> None:
    inserted = await seed_alpha_places()
    print(f"Alpha seed synced: {inserted} places")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
