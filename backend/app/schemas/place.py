from pydantic import BaseModel


class PlaceSummary(BaseModel):
    id: str
    name: str
    place_type: str
    description: str | None = None
    region: str | None = None
    source: str
    tags: dict[str, bool] = {}
    lat: float
    lon: float


class PlaceListResponse(BaseModel):
    data: list[PlaceSummary]
    total: int
    total_available: int = 0
    message: str
