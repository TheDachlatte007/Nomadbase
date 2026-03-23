from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import check_db, get_db
from app.models.expense import Expense
from app.models.import_job import ImportJob
from app.models.place import Place
from app.models.preference import UserPreference
from app.models.saved_place import SavedPlace
from app.models.trip import Trip
from app.models.visit import Visit
from app.schemas.admin import (
    ImportJobItem,
    ImportJobResponse,
    ImportJobListResponse,
    ImportRequest,
    ImportStatusResponse,
    PreferencesResponse,
    PreferencePayload,
    SystemStatusResponse,
)
from app.services.import_jobs import run_import_job

router = APIRouter()


PREFERENCE_DEFAULTS = PreferencePayload()


def _serialize_import_job(job: ImportJob) -> ImportJobItem:
    return ImportJobItem(
        id=str(job.id),
        city=job.city,
        country=job.country,
        region=job.region,
        status=job.status,
        imported_count=int(job.imported_count or 0),
        total_elements=int(job.total_elements or 0),
        error=job.error,
        created_at=job.created_at,
        finished_at=job.finished_at,
    )


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
    latest_successful_import = (
        select(
            ImportJob.region.label("region"),
            func.max(ImportJob.finished_at).label("last_imported_at"),
        )
        .where(ImportJob.status == "completed", ImportJob.region.is_not(None))
        .group_by(ImportJob.region)
        .subquery()
    )
    stmt = (
        select(
            Place.region,
            func.count(Place.id).label("place_count"),
            func.array_agg(func.distinct(Place.source)).label("sources"),
            latest_successful_import.c.last_imported_at,
        )
        .outerjoin(
            latest_successful_import,
            latest_successful_import.c.region == Place.region,
        )
        .where(Place.region.is_not(None))
        .group_by(Place.region, latest_successful_import.c.last_imported_at)
        .order_by(func.count(Place.id).desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    data = [
        {
            "region": row.region,
            "place_count": int(row.place_count),
            "sources": [source for source in (row.sources or []) if source],
            "last_imported_at": row.last_imported_at,
        }
        for row in rows
    ]
    return ImportStatusResponse(
        data=data,
        total=len(data),
        message="Imported regions" if data else "No imported regions yet",
    )


@router.get("/import-jobs", response_model=ImportJobListResponse)
async def list_import_jobs(db: AsyncSession = Depends(get_db)):
    stmt = select(ImportJob).order_by(ImportJob.created_at.desc()).limit(20)
    rows = (await db.execute(stmt)).scalars().all()
    data = [_serialize_import_job(job) for job in rows]
    return ImportJobListResponse(
        data=data,
        total=len(data),
        message="Recent import jobs" if data else "No import jobs yet",
    )


@router.get("/import-jobs/{job_id}", response_model=ImportJobResponse)
async def get_import_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await db.get(ImportJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Import job not found")

    return ImportJobResponse(data=_serialize_import_job(job), message="Import job")


@router.post(
    "/imports",
    response_model=ImportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_import(
    payload: ImportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    normalized_city = payload.city.strip()
    normalized_country = payload.country.strip() if payload.country else None

    if not normalized_city:
        raise HTTPException(status_code=422, detail="City is required")

    job = ImportJob(city=normalized_city, country=normalized_country, status="queued")
    db.add(job)
    await db.commit()
    await db.refresh(job)
    background_tasks.add_task(run_import_job, job.id)
    return ImportJobResponse(
        data=_serialize_import_job(job),
        message="Import queued in background",
    )


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
