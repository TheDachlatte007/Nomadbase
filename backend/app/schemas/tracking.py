from __future__ import annotations

from datetime import date as date_type, datetime

from pydantic import BaseModel, Field


class ExpenseCreateRequest(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(default="EUR", max_length=3, min_length=3)
    category: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=4000)
    place_id: str | None = None
    trip_id: str | None = None
    date: date_type | None = None


class ExpenseResponse(BaseModel):
    id: str
    amount: float
    currency: str
    category: str
    description: str | None = None
    place_id: str | None = None
    place_name: str | None = None
    city: str | None = None
    trip_id: str | None = None
    trip_name: str | None = None
    date: date_type
    created_at: datetime
    updated_at: datetime | None = None


class ExpenseListResponse(BaseModel):
    data: list[ExpenseResponse]
    total: int
    message: str


class ExpenseSummaryItem(BaseModel):
    category: str
    total: float


class ExpenseSummaryResponse(BaseModel):
    data: list[ExpenseSummaryItem]
    total_amount: float
    currency: str
    message: str


class VisitCreateRequest(BaseModel):
    place_id: str
    trip_id: str | None = None
    visited_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=4000)


class VisitResponse(BaseModel):
    id: str
    place_id: str
    place_name: str
    city: str | None = None
    trip_id: str | None = None
    trip_name: str | None = None
    visited_at: datetime
    notes: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class VisitListResponse(BaseModel):
    data: list[VisitResponse]
    total: int
    message: str
