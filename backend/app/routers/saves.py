from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_saved_places():
    return {"data": [], "message": "Saved places — not yet implemented"}


@router.post("/")
async def save_place():
    return {"message": "Save place — not yet implemented"}
