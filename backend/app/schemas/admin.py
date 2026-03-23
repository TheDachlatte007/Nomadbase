from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class PreferencePayload(BaseModel):
    interests: list[str] = Field(default_factory=list)
    dietary_filters: list[str] = Field(default_factory=list)
    budget_level: str = "balanced"


class PreferencesResponse(BaseModel):
    data: PreferencePayload
    message: str


class ImportStatusItem(BaseModel):
    region: str
    place_count: int
    sources: list[str]
    last_imported_at: datetime | None = None


class ImportStatusResponse(BaseModel):
    data: list[ImportStatusItem]
    total: int
    message: str


class ImportJobItem(BaseModel):
    id: str
    city: str
    country: str | None = None
    region: str | None = None
    status: str
    imported_count: int
    total_elements: int
    error: str | None = None
    created_at: datetime
    finished_at: datetime | None = None


class ImportJobListResponse(BaseModel):
    data: list[ImportJobItem]
    total: int
    message: str


class SystemStatusResponse(BaseModel):
    status: str
    database: bool
    alpha_seed_enabled: bool
    metrics: dict[str, int]


class ImportRequest(BaseModel):
    city: str
    country: Optional[str] = None


class ImportResult(BaseModel):
    job_id: str
    status: str
    region: str
    imported: int
    total_elements: int
    bbox: Optional[dict] = None
