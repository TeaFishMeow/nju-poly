from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

from app.appeals.router import router as appeals_router
from app.auth.router import router as auth_router
from app.core.config import settings
from app.forum.router import router as forum_router
from app.ledger.router import router as ledger_router
from app.markets.router import router as markets_router
from app.public_api.router import router as robot_router


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Campus entertainment prediction market API for NJUPoly.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(settings.media_storage_dir).mkdir(parents=True, exist_ok=True)
app.mount(settings.media_public_base_url, StaticFiles(directory=settings.media_storage_dir), name="media")

for api_router in (ledger_router, auth_router, markets_router, appeals_router, robot_router, forum_router):
    app.include_router(api_router)


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="api",
        version=settings.app_version,
        database=settings.safe_database_label,
    )
