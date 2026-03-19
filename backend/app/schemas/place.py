from pydantic import BaseModel


class PlaceSummary(BaseModel):
    id: str
    name: str
    place_type: str
    description: str | None = None
    region: str | None = None
    source: str
    tags: dict = {}
    address: str | None = None
    cuisine: str | None = None
    context_line: str | None = None
    website_url: str | None = None
    wikipedia_url: str | None = None
    wikidata_id: str | None = None
    lat: float
    lon: float


class PlaceListResponse(BaseModel):
    data: list[PlaceSummary]
    total: int
    total_available: int = 0
    message: str
