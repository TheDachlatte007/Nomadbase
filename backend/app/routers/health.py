from fastapi import APIRouter, Response, status
from app.db import check_db
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(response: Response):
    db_ok = await check_db()
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="ok" if db_ok else "error",
        database=db_ok,
        version="0.1.0",
    )
