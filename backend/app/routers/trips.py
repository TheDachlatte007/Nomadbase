from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_trips():
    return {"data": [], "message": "Trips — not yet implemented"}


@router.post("/")
async def create_trip():
    return {"message": "Create trip — not yet implemented"}
