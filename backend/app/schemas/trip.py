from __future__ import annotations

from datetime import date as date_type, datetime
from typing import Optional

from pydantic import BaseModel, Field


class TripUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    start_date: Optional[date_type] = None
    end_date: Optional[date_type] = None
    notes: Optional[str] = Field(default=None, max_length=4000)


class TripCityCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    country: str | None = Field(default=None, max_length=100)
    lat: float | None = None
    lon: float | None = None


class TripParticipantCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=1000)


class TripCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    start_date: date_type | None = None
    end_date: date_type | None = None
    notes: str | None = Field(default=None, max_length=4000)


class TripCityResponse(BaseModel):
    id: str
    name: str
    country: str | None = None
    lat: float | None = None
    lon: float | None = None
    created_at: datetime
    updated_at: datetime | None = None


class TripParticipantResponse(BaseModel):
    id: str
    name: str
    note: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class TripResponse(BaseModel):
    id: str
    name: str
    start_date: date_type | None = None
    end_date: date_type | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    cities: list[TripCityResponse]
    participants: list[TripParticipantResponse]


class TripListResponse(BaseModel):
    data: list[TripResponse]
    total: int
    message: str
