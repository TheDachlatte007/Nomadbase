from datetime import timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.expense import Expense
from app.models.place import Place
from app.models.trip import Trip
from app.models.visit import Visit
from app.schemas.tracking import (
    ExpenseCreateRequest,
    ExpenseListResponse,
    ExpenseResponse,
    ExpenseSummaryResponse,
    VisitCreateRequest,
    VisitListResponse,
    VisitResponse,
)

router = APIRouter()


def _parse_uuid(value: str, field_name: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} must be a valid UUID",
        ) from exc


def _expense_stmt():
    return (
        select(
            Expense.id,
            Expense.amount,
            Expense.currency,
            Expense.category,
            Expense.description,
            Expense.place_id,
            Expense.trip_id,
            Expense.date,
            Expense.created_at,
            Expense.updated_at,
            Place.name.label("place_name"),
            Place.region.label("city"),
            Trip.name.label("trip_name"),
        )
        .outerjoin(Place, Place.id == Expense.place_id)
        .outerjoin(Trip, Trip.id == Expense.trip_id)
    )


def _visit_stmt():
    return (
        select(
            Visit.id,
            Visit.place_id,
            Visit.trip_id,
            Visit.visited_at,
            Visit.notes,
            Visit.created_at,
            Visit.updated_at,
            Place.name.label("place_name"),
            Place.region.label("city"),
            Trip.name.label("trip_name"),
        )
        .join(Place, Place.id == Visit.place_id)
        .outerjoin(Trip, Trip.id == Visit.trip_id)
    )


async def _require_place(db: AsyncSession, place_id: UUID) -> None:
    if await db.get(Place, place_id) is None:
        raise HTTPException(status_code=404, detail="Place not found")


async def _require_trip(db: AsyncSession, trip_id: UUID) -> None:
    if await db.get(Trip, trip_id) is None:
        raise HTTPException(status_code=404, detail="Trip not found")


def _serialize_expense(row) -> dict:
    return {
        "id": str(row.id),
        "amount": float(row.amount),
        "currency": row.currency,
        "category": row.category,
        "description": row.description,
        "place_id": str(row.place_id) if row.place_id else None,
        "place_name": row.place_name,
        "city": row.city,
        "trip_id": str(row.trip_id) if row.trip_id else None,
        "trip_name": row.trip_name,
        "date": row.date,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _serialize_visit(row) -> dict:
    return {
        "id": str(row.id),
        "place_id": str(row.place_id),
        "place_name": row.place_name,
        "city": row.city,
        "trip_id": str(row.trip_id) if row.trip_id else None,
        "trip_name": row.trip_name,
        "visited_at": row.visited_at,
        "notes": row.notes,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _apply_city_filter(stmt, city: str | None):
    if city:
        stmt = stmt.where(Place.region.ilike(f"%{city.strip()}%"))
    return stmt


@router.get("/expenses/summary", response_model=ExpenseSummaryResponse)
async def expense_summary(
    trip_id: str | None = None,
    city: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(
            Expense.category,
            func.coalesce(func.sum(Expense.amount), 0).label("total"),
        )
        .outerjoin(Place, Place.id == Expense.place_id)
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc(), Expense.category.asc())
    )

    if trip_id:
        stmt = stmt.where(Expense.trip_id == _parse_uuid(trip_id, "trip_id"))

    stmt = _apply_city_filter(stmt, city)

    result = await db.execute(stmt)
    rows = result.all()
    data = [{"category": row.category, "total": float(row.total)} for row in rows]

    return ExpenseSummaryResponse(
        data=data,
        total_amount=round(sum(item["total"] for item in data), 2),
        currency="EUR",
        message="Expense overview" if data else "No expenses recorded yet",
    )


@router.get("/expenses", response_model=ExpenseListResponse)
async def list_expenses(
    trip_id: str | None = None,
    city: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = _expense_stmt().order_by(Expense.date.desc(), Expense.created_at.desc())

    if trip_id:
        stmt = stmt.where(Expense.trip_id == _parse_uuid(trip_id, "trip_id"))

    stmt = _apply_city_filter(stmt, city)

    result = await db.execute(stmt)
    data = [_serialize_expense(row) for row in result.all()]
    return ExpenseListResponse(
        data=data,
        total=len(data),
        message="Expenses" if data else "No expenses yet",
    )


@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def record_expense(
    payload: ExpenseCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    place_uuid = _parse_uuid(payload.place_id, "place_id") if payload.place_id else None
    trip_uuid = _parse_uuid(payload.trip_id, "trip_id") if payload.trip_id else None

    if place_uuid:
        await _require_place(db, place_uuid)
    if trip_uuid:
        await _require_trip(db, trip_uuid)

    expense_kwargs = {
        "amount": payload.amount,
        "currency": "EUR",
        "category": payload.category,
        "description": payload.description,
        "place_id": place_uuid,
        "trip_id": trip_uuid,
    }
    if payload.date is not None:
        expense_kwargs["date"] = payload.date

    expense = Expense(**expense_kwargs)
    db.add(expense)
    await db.commit()

    result = await db.execute(_expense_stmt().where(Expense.id == expense.id))
    return ExpenseResponse(**_serialize_expense(result.one()))


@router.get("/visits", response_model=VisitListResponse)
async def list_visits(
    trip_id: str | None = None,
    city: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = _visit_stmt().order_by(Visit.visited_at.desc(), Visit.created_at.desc())

    if trip_id:
        stmt = stmt.where(Visit.trip_id == _parse_uuid(trip_id, "trip_id"))

    stmt = _apply_city_filter(stmt, city)

    result = await db.execute(stmt)
    data = [_serialize_visit(row) for row in result.all()]
    return VisitListResponse(
        data=data,
        total=len(data),
        message="Visits" if data else "No visits yet",
    )


@router.post("/visits", response_model=VisitResponse, status_code=status.HTTP_201_CREATED)
async def log_visit(
    payload: VisitCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    place_uuid = _parse_uuid(payload.place_id, "place_id")
    trip_uuid = _parse_uuid(payload.trip_id, "trip_id") if payload.trip_id else None

    await _require_place(db, place_uuid)
    if trip_uuid:
        await _require_trip(db, trip_uuid)

    visited_at = payload.visited_at
    if visited_at and visited_at.tzinfo is None:
        visited_at = visited_at.replace(tzinfo=timezone.utc)

    visit_kwargs = {
        "place_id": place_uuid,
        "trip_id": trip_uuid,
        "notes": payload.notes,
    }
    if visited_at is not None:
        visit_kwargs["visited_at"] = visited_at

    visit = Visit(**visit_kwargs)
    db.add(visit)
    await db.commit()

    result = await db.execute(_visit_stmt().where(Visit.id == visit.id))
    return VisitResponse(**_serialize_visit(result.one()))
