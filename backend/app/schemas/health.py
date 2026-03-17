from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str  # "ok" or "error"
    database: bool
    version: str
