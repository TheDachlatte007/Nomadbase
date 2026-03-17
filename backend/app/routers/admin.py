from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import check_db, get_db
from app.models.expense import Expense
from app.models.place import Place
from app.models.preference import UserPreference
from app.models.saved_place import SavedPlace
from app.models.trip import Trip
from app.models.visit import Visit
from app.schemas.admin import (
    ImportRequest,
    ImportResult,
    ImportStatusResponse,
    PreferencesResponse,
    PreferencePayload,
    SystemStatusResponse,
)
from app.services.overpass import import_city

router = APIRouter()


PREFERENCE_DEFAULTS = PreferencePayload()


@router.get("/status", response_model=SystemStatusResponse)
async def system_status(db: AsyncSession = Depends(get_db)):
    database_ok = await check_db()
    database_size = await db.scalar(select(func.pg_database_size(func.current_database())))
    imported_regions = await db.scalar(
        select(func.count(func.distinct(Place.region))).where(Place.region.is_not(None))
    )
    counts = {
        "places": await db.scalar(select(func.count()).select_from(Place)),
        "saved_places": await db.scalar(select(func.count()).select_from(SavedPlace)),
        "trips": await db.scalar(select(func.count()).select_from(Trip)),
        "expenses": await db.scalar(select(func.count()).select_from(Expense)),
        "visits": await db.scalar(select(func.count()).select_from(Visit)),
        "imported_regions": imported_regions,
        "database_size_mb": int((database_size or 0) / (1024 * 1024)),
    }
    return SystemStatusResponse(
        status="ok" if database_ok else "degraded",
        database=database_ok,
        alpha_seed_enabled=settings.SEED_ALPHA_DATA,
        metrics={key: int(value or 0) for key, value in counts.items()},
    )


@router.get("/imports", response_model=ImportStatusResponse)
async def list_imports(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Place.region,
            func.count(Place.id).label("place_count"),
            func.array_agg(func.distinct(Place.source)).label("sources"),
        )
        .where(Place.region.is_not(None))
        .group_by(Place.region)
        .order_by(func.count(Place.id).desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    data = [
        {
            "region": row.region,
            "place_count": int(row.place_count),
            "sources": [source for source in (row.sources or []) if source],
        }
        for row in rows
    ]
    return ImportStatusResponse(
        data=data,
        total=len(data),
        message="Imported regions" if data else "No imported regions yet",
    )


@router.post("/imports", response_model=ImportResult)
async def trigger_import(
    payload: ImportRequest, db: AsyncSession = Depends(get_db)
):
    try:
        result = await import_city(payload.city, payload.country, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Import failed: {exc}"
        ) from exc
    return ImportResult(**result)


async def _load_preferences(db: AsyncSession) -> PreferencePayload:
    result = await db.execute(select(UserPreference))
    prefs = {row.key: row.value for row in result.scalars().all()}
    return PreferencePayload(
        interests=prefs.get("interests", PREFERENCE_DEFAULTS.interests),
        dietary_filters=prefs.get(
            "dietary_filters", PREFERENCE_DEFAULTS.dietary_filters
        ),
        budget_level=prefs.get("budget_level", PREFERENCE_DEFAULTS.budget_level),
    )


@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(db: AsyncSession = Depends(get_db)):
    data = await _load_preferences(db)
    return PreferencesResponse(data=data, message="User preferences")


@router.put("/preferences", response_model=PreferencesResponse)
async def update_preferences(
    payload: PreferencePayload, db: AsyncSession = Depends(get_db)
):
    for key, value in payload.model_dump().items():
        stmt = pg_insert(UserPreference).values(key=key, value=value)
        stmt = stmt.on_conflict_do_update(
            index_elements=["key"],
            set_={"value": stmt.excluded.value},
        )
        await db.execute(stmt)

    await db.commit()
    data = await _load_preferences(db)
    return PreferencesResponse(data=data, message="User preferences updated")
