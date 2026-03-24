from collections import defaultdict
from datetime import timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.models.place import Place
from app.models.trip import Trip
from app.models.trip_participant import TripParticipant
from app.models.visit import Visit
from app.schemas.tracking import (
    ExpenseCreateRequest,
    ExpenseListResponse,
    ExpenseRebalanceRequest,
    ExpenseRebalanceResponse,
    ExpenseResponse,
    ExpenseSummaryResponse,
    ExpenseUpdateRequest,
    TripBalanceParticipant,
    TripSettlementCurrencyGroup,
    TripSettlementResponse,
    TripSettlementTransfer,
    VisitCreateRequest,
    VisitListResponse,
    VisitResponse,
)

router = APIRouter()
_CENT = Decimal("0.01")


def _parse_uuid(value: str, field_name: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} must be a valid UUID",
        ) from exc


async def _require_place(db: AsyncSession, place_id: UUID) -> None:
    if await db.get(Place, place_id) is None:
        raise HTTPException(status_code=404, detail="Place not found")


async def _require_trip(db: AsyncSession, trip_id: UUID) -> Trip:
    trip = await db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


async def _load_trip_participants(
    db: AsyncSession, trip_id: UUID
) -> dict[UUID, TripParticipant]:
    result = await db.execute(
        select(TripParticipant).where(TripParticipant.trip_id == trip_id)
    )
    return {participant.id: participant for participant in result.scalars().all()}


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
            Expense.paid_by_participant_id,
            Expense.date,
            Expense.created_at,
            Expense.updated_at,
            Place.name.label("place_name"),
            Place.region.label("city"),
            Trip.name.label("trip_name"),
            TripParticipant.name.label("paid_by_participant_name"),
        )
        .outerjoin(Place, Place.id == Expense.place_id)
        .outerjoin(Trip, Trip.id == Expense.trip_id)
        .outerjoin(
            TripParticipant,
            TripParticipant.id == Expense.paid_by_participant_id,
        )
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


def _apply_city_filter(stmt, city: str | None):
    if city:
        stmt = stmt.where(Place.region.ilike(f"%{city.strip()}%"))
    return stmt


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


async def _load_splits_for_expenses(
    db: AsyncSession, expense_ids: list[UUID]
) -> dict[UUID, list[dict]]:
    if not expense_ids:
        return {}

    result = await db.execute(
        select(
            ExpenseSplit.expense_id,
            ExpenseSplit.participant_id,
            ExpenseSplit.share_amount,
            TripParticipant.name.label("participant_name"),
        )
        .join(TripParticipant, TripParticipant.id == ExpenseSplit.participant_id)
        .where(ExpenseSplit.expense_id.in_(expense_ids))
        .order_by(TripParticipant.created_at.asc(), TripParticipant.name.asc())
    )

    grouped: dict[UUID, list[dict]] = defaultdict(list)
    for row in result.all():
        grouped[row.expense_id].append(
            {
                "participant_id": str(row.participant_id),
                "participant_name": row.participant_name,
                "amount": float(row.share_amount),
            }
        )
    return grouped


async def _load_split_participant_ids(
    db: AsyncSession,
    expense_id: UUID,
) -> list[str]:
    result = await db.execute(
        select(ExpenseSplit.participant_id).where(ExpenseSplit.expense_id == expense_id)
    )
    return [str(participant_id) for participant_id in result.scalars().all()]


async def _serialize_expenses(db: AsyncSession, rows) -> list[dict]:
    expense_ids = [row.id for row in rows]
    splits_by_expense = await _load_splits_for_expenses(db, expense_ids)

    data = []
    for row in rows:
        splits = splits_by_expense.get(row.id, [])
        data.append(
            {
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
                "paid_by_participant_id": (
                    str(row.paid_by_participant_id)
                    if row.paid_by_participant_id
                    else None
                ),
                "paid_by_participant_name": row.paid_by_participant_name,
                "split_participant_ids": [
                    split["participant_id"] for split in splits
                ],
                "split_participant_names": [
                    split["participant_name"] for split in splits
                ],
                "date": row.date,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
        )
    return data


def _split_amount_evenly(total: Decimal, participant_ids: list[UUID]) -> dict[UUID, Decimal]:
    quantized_total = total.quantize(_CENT, rounding=ROUND_HALF_UP)
    count = len(participant_ids)
    base = (quantized_total / count).quantize(_CENT, rounding=ROUND_HALF_UP)
    shares = {participant_id: base for participant_id in participant_ids}
    assigned = sum(shares.values(), Decimal("0.00"))
    remainder_cents = int((quantized_total - assigned) / _CENT)

    for participant_id in participant_ids[:remainder_cents]:
        shares[participant_id] += _CENT

    return shares


def _build_settlement_transfers(participants: list[dict]) -> list[dict]:
    debtors = []
    creditors = []
    for participant in participants:
        net = Decimal(str(participant["net"]))
        if net < 0:
            debtors.append(
                {
                    "participant_id": participant["participant_id"],
                    "participant_name": participant["participant_name"],
                    "amount": -net,
                }
            )
        elif net > 0:
            creditors.append(
                {
                    "participant_id": participant["participant_id"],
                    "participant_name": participant["participant_name"],
                    "amount": net,
                }
            )

    transfers = []
    debtor_index = 0
    creditor_index = 0
    while debtor_index < len(debtors) and creditor_index < len(creditors):
        debtor = debtors[debtor_index]
        creditor = creditors[creditor_index]
        amount = min(debtor["amount"], creditor["amount"]).quantize(
            _CENT, rounding=ROUND_HALF_UP
        )
        if amount > 0:
            transfers.append(
                {
                    "from_participant_id": debtor["participant_id"],
                    "from_participant_name": debtor["participant_name"],
                    "to_participant_id": creditor["participant_id"],
                    "to_participant_name": creditor["participant_name"],
                    "amount": float(amount),
                }
            )
        debtor["amount"] -= amount
        creditor["amount"] -= amount
        if debtor["amount"] <= Decimal("0.00"):
            debtor_index += 1
        if creditor["amount"] <= Decimal("0.00"):
            creditor_index += 1

    return transfers


async def _prepare_expense_payload(
    db: AsyncSession,
    payload: ExpenseCreateRequest | ExpenseUpdateRequest,
) -> tuple[dict, list[UUID]]:
    place_uuid = _parse_uuid(payload.place_id, "place_id") if payload.place_id else None
    trip_uuid = _parse_uuid(payload.trip_id, "trip_id") if payload.trip_id else None
    paid_by_uuid = (
        _parse_uuid(payload.paid_by_participant_id, "paid_by_participant_id")
        if payload.paid_by_participant_id
        else None
    )
    split_participant_ids = [
        _parse_uuid(participant_id, "split_participant_ids")
        for participant_id in payload.split_participant_ids
    ]

    if place_uuid:
        await _require_place(db, place_uuid)

    trip_participants: dict[UUID, TripParticipant] = {}
    if trip_uuid:
        await _require_trip(db, trip_uuid)
        trip_participants = await _load_trip_participants(db, trip_uuid)

    if (paid_by_uuid or split_participant_ids) and not trip_uuid:
        raise HTTPException(
            status_code=422,
            detail="Participant-based expense splitting requires a linked trip",
        )

    if paid_by_uuid and paid_by_uuid not in trip_participants:
        raise HTTPException(status_code=404, detail="Paying participant not found")

    if split_participant_ids:
        invalid_ids = [
            participant_id
            for participant_id in split_participant_ids
            if participant_id not in trip_participants
        ]
        if invalid_ids:
            raise HTTPException(status_code=404, detail="Split participant not found")

    split_targets = split_participant_ids.copy()
    if trip_uuid and paid_by_uuid and not split_targets:
        split_targets = [paid_by_uuid]

    expense_fields = {
        "amount": payload.amount,
        "currency": payload.currency.upper(),
        "category": payload.category,
        "description": payload.description,
        "place_id": place_uuid,
        "trip_id": trip_uuid,
        "paid_by_participant_id": paid_by_uuid,
    }
    if payload.date is not None:
        expense_fields["date"] = payload.date
    return expense_fields, split_targets


async def _replace_expense_splits(
    db: AsyncSession,
    expense_id: UUID,
    amount: Decimal,
    participant_ids: list[UUID],
) -> None:
    existing = await db.execute(
        select(ExpenseSplit).where(ExpenseSplit.expense_id == expense_id)
    )
    for split in existing.scalars().all():
        await db.delete(split)

    if not participant_ids:
        return

    split_map = _split_amount_evenly(amount, participant_ids)
    for participant_id, share_amount in split_map.items():
        db.add(
            ExpenseSplit(
                expense_id=expense_id,
                participant_id=participant_id,
                share_amount=share_amount,
            )
        )


async def _expense_split_ids_for_trip(
    db: AsyncSession,
    trip_id: UUID,
) -> dict[UUID, set[UUID]]:
    result = await db.execute(
        select(Expense.id, ExpenseSplit.participant_id)
        .outerjoin(ExpenseSplit, ExpenseSplit.expense_id == Expense.id)
        .where(Expense.trip_id == trip_id)
    )
    split_map: dict[UUID, set[UUID]] = defaultdict(set)
    for expense_id, participant_id in result.all():
        if participant_id is not None:
            split_map[expense_id].add(participant_id)
        else:
            split_map.setdefault(expense_id, set())
    return split_map


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


@router.get("/expenses/settlements", response_model=TripSettlementResponse)
async def expense_settlement(
    trip_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    trip_uuid = _parse_uuid(trip_id, "trip_id")
    trip = await _require_trip(db, trip_uuid)

    participants = await _load_trip_participants(db, trip_uuid)
    if not participants:
        return TripSettlementResponse(
            trip_id=str(trip.id),
            trip_name=trip.name,
            data=[],
            message="No participants added yet",
        )

    expense_result = await db.execute(
        select(
            Expense.id,
            Expense.amount,
            Expense.currency,
            Expense.paid_by_participant_id,
        ).where(Expense.trip_id == trip_uuid)
    )
    expenses = expense_result.all()
    expense_ids = [row.id for row in expenses]

    split_result = await db.execute(
        select(
            ExpenseSplit.expense_id,
            ExpenseSplit.participant_id,
            ExpenseSplit.share_amount,
        ).where(ExpenseSplit.expense_id.in_(expense_ids) if expense_ids else False)
    )

    currencies: dict[str, dict] = defaultdict(
        lambda: {
            "total_expenses": Decimal("0.00"),
            "participants": {
                participant_id: {
                    "participant_id": str(participant_id),
                    "participant_name": participant.name,
                    "paid": Decimal("0.00"),
                    "owed": Decimal("0.00"),
                }
                for participant_id, participant in participants.items()
            },
        }
    )

    expense_currency: dict[UUID, str] = {}
    for expense in expenses:
        currency_bucket = currencies[expense.currency]
        amount = Decimal(str(expense.amount)).quantize(_CENT, rounding=ROUND_HALF_UP)
        currency_bucket["total_expenses"] += amount
        expense_currency[expense.id] = expense.currency
        if expense.paid_by_participant_id in participants:
            currency_bucket["participants"][expense.paid_by_participant_id]["paid"] += amount

    for split in split_result.all():
        currency = expense_currency.get(split.expense_id)
        if not currency or split.participant_id not in participants:
            continue
        currencies[currency]["participants"][split.participant_id]["owed"] += Decimal(
            str(split.share_amount)
        ).quantize(_CENT, rounding=ROUND_HALF_UP)

    data = []
    for currency, bucket in currencies.items():
        participant_rows = []
        for participant in bucket["participants"].values():
            paid = participant["paid"].quantize(_CENT, rounding=ROUND_HALF_UP)
            owed = participant["owed"].quantize(_CENT, rounding=ROUND_HALF_UP)
            net = (paid - owed).quantize(_CENT, rounding=ROUND_HALF_UP)
            participant_rows.append(
                {
                    "participant_id": participant["participant_id"],
                    "participant_name": participant["participant_name"],
                    "paid": float(paid),
                    "owed": float(owed),
                    "net": float(net),
                }
            )

        participant_rows.sort(key=lambda item: item["participant_name"].lower())
        transfers = _build_settlement_transfers(participant_rows)
        data.append(
            TripSettlementCurrencyGroup(
                currency=currency,
                total_expenses=float(
                    bucket["total_expenses"].quantize(_CENT, rounding=ROUND_HALF_UP)
                ),
                participants=[
                    TripBalanceParticipant(**participant) for participant in participant_rows
                ],
                transfers=[
                    TripSettlementTransfer(**transfer) for transfer in transfers
                ],
            )
        )

    data.sort(key=lambda item: item.currency)
    return TripSettlementResponse(
        trip_id=str(trip.id),
        trip_name=trip.name,
        data=data,
        message="Trip settlement" if data else "No expenses for this trip yet",
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
    data = await _serialize_expenses(db, result.all())
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
    expense_fields, split_targets = await _prepare_expense_payload(db, payload)
    expense = Expense(**expense_fields)
    db.add(expense)
    await db.flush()
    await _replace_expense_splits(
        db,
        expense.id,
        Decimal(str(payload.amount)),
        split_targets,
    )

    await db.commit()

    result = await db.execute(_expense_stmt().where(Expense.id == expense.id))
    serialized = await _serialize_expenses(db, result.all())
    return ExpenseResponse(**serialized[0])


@router.patch("/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: str,
    payload: ExpenseUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    expense_uuid = _parse_uuid(expense_id, "expense_id")
    expense = await db.get(Expense, expense_uuid)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    provided_fields = payload.model_fields_set

    merged_payload = ExpenseCreateRequest(
        amount=payload.amount if payload.amount is not None else float(expense.amount),
        currency=payload.currency or expense.currency,
        category=payload.category or expense.category,
        description=(
            payload.description
            if "description" in provided_fields
            else expense.description
        ),
        place_id=(
            payload.place_id
            if "place_id" in provided_fields
            else (str(expense.place_id) if expense.place_id else None)
        ),
        trip_id=(
            payload.trip_id
            if "trip_id" in provided_fields
            else (str(expense.trip_id) if expense.trip_id else None)
        ),
        paid_by_participant_id=(
            payload.paid_by_participant_id
            if "paid_by_participant_id" in provided_fields
            else (
                str(expense.paid_by_participant_id)
                if expense.paid_by_participant_id
                else None
            )
        ),
        split_participant_ids=(
            payload.split_participant_ids
            if "split_participant_ids" in provided_fields
            else await _load_split_participant_ids(db, expense.id)
        ),
        date=payload.date if "date" in provided_fields else expense.date,
    )

    expense_fields, split_targets = await _prepare_expense_payload(db, merged_payload)
    for field, value in expense_fields.items():
        setattr(expense, field, value)

    await _replace_expense_splits(
        db,
        expense.id,
        Decimal(str(merged_payload.amount)),
        split_targets,
    )
    await db.commit()

    result = await db.execute(_expense_stmt().where(Expense.id == expense.id))
    serialized = await _serialize_expenses(db, result.all())
    return ExpenseResponse(**serialized[0])


@router.post("/expenses/rebalance", response_model=ExpenseRebalanceResponse)
async def rebalance_expenses(
    payload: ExpenseRebalanceRequest,
    db: AsyncSession = Depends(get_db),
):
    trip_uuid = _parse_uuid(payload.trip_id, "trip_id")
    await _require_trip(db, trip_uuid)
    trip_participants = await _load_trip_participants(db, trip_uuid)
    participant_ids = list(trip_participants.keys())
    if not participant_ids:
        raise HTTPException(
            status_code=422,
            detail="Add participants to the trip before re-splitting expenses",
        )

    selected_expense_ids = {
        _parse_uuid(expense_id, "expense_ids") for expense_id in payload.expense_ids
    }
    expense_rows = (
        await db.execute(
            select(Expense.id, Expense.amount)
            .where(Expense.trip_id == trip_uuid)
            .order_by(Expense.date.desc(), Expense.created_at.desc())
        )
    ).all()

    if selected_expense_ids:
        expense_rows = [row for row in expense_rows if row.id in selected_expense_ids]

    if not expense_rows:
        return ExpenseRebalanceResponse(
            trip_id=str(trip_uuid),
            updated_count=0,
            skipped_count=0,
            participant_count=len(participant_ids),
            message="No matching expenses found for re-splitting",
        )

    current_split_map = await _expense_split_ids_for_trip(db, trip_uuid)
    target_participant_set = set(participant_ids)
    updated_count = 0
    skipped_count = 0

    for row in expense_rows:
        if current_split_map.get(row.id, set()) == target_participant_set:
            skipped_count += 1
            continue

        await _replace_expense_splits(
            db,
            row.id,
            Decimal(str(row.amount)),
            participant_ids,
        )
        updated_count += 1

    await db.commit()
    message = (
        f"Re-split {updated_count} expense(s) across {len(participant_ids)} participant(s)"
        if updated_count
        else "Selected expenses already match the current trip crew"
    )
    return ExpenseRebalanceResponse(
        trip_id=str(trip_uuid),
        updated_count=updated_count,
        skipped_count=skipped_count,
        participant_count=len(participant_ids),
        message=message,
    )


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


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: str, db: AsyncSession = Depends(get_db)):
    expense_uuid = _parse_uuid(expense_id, "expense_id")
    expense = await db.get(Expense, expense_uuid)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    await db.delete(expense)
    await db.commit()


@router.delete("/visits/{visit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_visit(visit_id: str, db: AsyncSession = Depends(get_db)):
    visit_uuid = _parse_uuid(visit_id, "visit_id")
    visit = await db.get(Visit, visit_uuid)
    if visit is None:
        raise HTTPException(status_code=404, detail="Visit not found")
    await db.delete(visit)
    await db.commit()
