from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def system_status():
    return {"message": "System status — not yet implemented"}


@router.get("/imports")
async def list_imports():
    return {"data": [], "message": "Import status — not yet implemented"}


@router.post("/imports")
async def trigger_import():
    return {"message": "Trigger import — not yet implemented"}


@router.get("/preferences")
async def get_preferences():
    return {"data": {}, "message": "User preferences — not yet implemented"}
