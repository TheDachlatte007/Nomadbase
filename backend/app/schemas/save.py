from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.place import PlaceSummary

SaveStatus = Literal["want_to_visit", "visited", "favorite"]


class SavePlaceRequest(BaseModel):
    place_id: str
    trip_id: str | None = None
    status: SaveStatus
    notes: str | None = Field(default=None, max_length=2000)


class UpdateSavedPlaceRequest(BaseModel):
    trip_id: str | None = None
    status: SaveStatus | None = None
    notes: str | None = Field(default=None, max_length=2000)


class SavedPlaceResponse(BaseModel):
    id: str
    place_id: str
    trip_id: str | None = None
    trip_name: str | None = None
    status: SaveStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    place: PlaceSummary


class SavedPlaceListResponse(BaseModel):
    data: list[SavedPlaceResponse]
    total: int
    message: str
