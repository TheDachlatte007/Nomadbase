from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def map_root():
    return {
        "message": "Map endpoints",
        "endpoints": ["/places", "/places/nearby"],
    }


@router.get("/places")
async def list_places():
    return {"data": [], "message": "POI listing — not yet implemented"}


@router.get("/places/nearby")
async def nearby_places():
    return {"data": [], "message": "Nearby POI search — not yet implemented"}
