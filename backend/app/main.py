from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.config import settings
from app.routers import health, map, saves, trips, tracking, admin

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

allow_origins = settings.cors_allow_origins_list
allow_all_origins = "*" in allow_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else allow_origins,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.ENABLE_GZIP:
    app.add_middleware(GZipMiddleware, minimum_size=1200)

trusted_hosts = settings.trusted_hosts_list
if trusted_hosts != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

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
