from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.router import api_router
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.services.logging import configure_logging
from app.services.monitoring import init_sentry

configure_logging()
init_sentry()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(ErrorHandlerMiddleware)

app.include_router(api_router, prefix=settings.api_v1_prefix)

static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

@app.on_event("startup")
async def validate_settings():
    settings.validate_for_env()
