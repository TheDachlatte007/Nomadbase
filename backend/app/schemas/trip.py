from __future__ import annotations

from datetime import date as date_type, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.admin import ImportJobItem


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
    notes: str | None = Field(default=None, max_length=2000)


class TripCityReorderRequest(BaseModel):
    city_ids: list[str] = Field(min_length=1)


class TripCityUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    country: str | None = Field(default=None, max_length=100)
    lat: float | None = None
    lon: float | None = None
    notes: str | None = Field(default=None, max_length=2000)


class TripCoverageImportRequest(BaseModel):
    city_ids: list[str] = Field(default_factory=list)


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
    sort_order: int
    notes: str | None = None
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


class TripOverviewCityResponse(BaseModel):
    id: str
    name: str
    country: str | None = None
    sort_order: int
    lat: float | None = None
    lon: float | None = None
    saved_count: int
    want_to_visit_count: int
    visited_count: int
    favorite_count: int
    place_type_counts: dict[str, int]
    preview_places: list[str]
    notes: str | None = None
    highlights: list[str]
    coverage: "TripOverviewCityCoverageResponse"
    places: list["TripOverviewPlaceResponse"]
    suggested_unassigned_places: list["TripOverviewSuggestedPlaceResponse"]
    discovery_candidates: list["TripOverviewDiscoveryPlaceResponse"]


class TripOverviewPlaceResponse(BaseModel):
    saved_place_id: str
    place_id: str
    name: str
    place_type: str
    status: str
    notes: str | None = None
    lat: float
    lon: float
    city_id: str | None = None
    city_name: str | None = None


class TripOverviewSuggestedPlaceResponse(BaseModel):
    saved_place_id: str
    place_id: str
    name: str
    place_type: str
    status: str
    notes: str | None = None
    lat: float
    lon: float
    suggestion_score: int


class TripOverviewDiscoveryPlaceResponse(BaseModel):
    place_id: str
    name: str
    place_type: str
    description: str | None = None
    region: str | None = None
    lat: float
    lon: float
    distance_km: float | None = None
    score: int
    reason: str


class TripOverviewCityCoverageResponse(BaseModel):
    level: str
    local_place_count: int
    region_match_count: int
    nearby_place_count: int
    import_region_hint: str
    summary: str
    needs_import: bool
    last_imported_at: datetime | None = None
    active_import_job_id: str | None = None
    active_import_status: str | None = None
    active_import_created_at: datetime | None = None


class TripOverviewCoverageSummaryResponse(BaseModel):
    ready: int
    usable: int
    thin: int
    missing: int
    needs_import: int
    unmapped_cities: int
    queued_imports: int
    running_imports: int
    route_readiness: str


class TripOverviewResponse(BaseModel):
    trip_id: str
    trip_name: str
    participant_count: int
    city_count: int
    total_saved_places: int
    assigned_saved_places: int
    unassigned_saved_places: int
    route_label: str
    route_distance_km: float | None = None
    cities_without_places: int
    cities_without_coordinates: int
    route_highlights: list[str]
    coverage_summary: TripOverviewCoverageSummaryResponse
    cities: list[TripOverviewCityResponse]
    unassigned_places: list[TripOverviewPlaceResponse]


class TripCoverageImportResponse(BaseModel):
    data: list[ImportJobItem]
    queued_count: int
    reused_count: int
    message: str


class TripListResponse(BaseModel):
    data: list[TripResponse]
    total: int
    message: str
