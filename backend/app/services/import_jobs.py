from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session_maker
from app.models.import_job import ImportJob
from app.services.overpass import import_city


async def _get_job(session: AsyncSession, job_id: UUID) -> ImportJob | None:
    return await session.get(ImportJob, job_id)


async def _mark_job(
    job_id: UUID,
    *,
    status: str,
    region: str | None = None,
    imported_count: int | None = None,
    total_elements: int | None = None,
    error: str | None = None,
    finished: bool = False,
) -> None:
    async with async_session_maker() as session:
        job = await _get_job(session, job_id)
        if job is None:
            return

        job.status = status
        if region is not None:
            job.region = region
        if imported_count is not None:
            job.imported_count = int(imported_count)
        if total_elements is not None:
            job.total_elements = int(total_elements)
        job.error = error
        job.finished_at = datetime.now(timezone.utc) if finished else None
        await session.commit()


async def run_import_job(job_id: UUID) -> None:
    async with async_session_maker() as session:
        job = await _get_job(session, job_id)
        if job is None:
            return

        job.status = "running"
        job.error = None
        job.finished_at = None
        city = job.city
        country = job.country
        await session.commit()

        try:
            result = await import_city(city, country, session)
            job.region = result["region"]
            job.status = "completed"
            job.imported_count = int(result.get("imported", 0) or 0)
            job.total_elements = int(result.get("total_elements", 0) or 0)
            job.error = None
            job.finished_at = datetime.now(timezone.utc)
            await session.commit()
        except ValueError as exc:
            await session.rollback()
            await _mark_job(job_id, status="failed", error=str(exc), finished=True)
        except Exception as exc:
            await session.rollback()
            await _mark_job(
                job_id,
                status="failed",
                error=f"Import failed: {exc}",
                finished=True,
            )
