from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.config import settings
from app.routers import health, map, saves, trips, tracking, admin

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(map.router, prefix="/api/map", tags=["map"])
app.include_router(saves.router, prefix="/api/saves", tags=["saves"])
app.include_router(trips.router, prefix="/api/trips", tags=["trips"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["tracking"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

frontend_dist = Path(__file__).resolve().parent / "static"

if frontend_dist.exists():
    index_file = frontend_dist / "index.html"

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(index_file)


    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        requested = (frontend_dist / full_path).resolve()
        try:
            requested.relative_to(frontend_dist.resolve())
        except ValueError:
            return FileResponse(index_file)

        if requested.is_file():
            return FileResponse(requested)

        return FileResponse(index_file)
