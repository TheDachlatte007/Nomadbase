from fastapi import APIRouter

router = APIRouter()


@router.get("/expenses")
async def list_expenses():
    return {"data": [], "message": "Expenses — not yet implemented"}


@router.post("/expenses")
async def record_expense():
    return {"message": "Record expense — not yet implemented"}


@router.get("/visits")
async def list_visits():
    return {"data": [], "message": "Visits — not yet implemented"}


@router.post("/visits")
async def log_visit():
    return {"message": "Log visit — not yet implemented"}
