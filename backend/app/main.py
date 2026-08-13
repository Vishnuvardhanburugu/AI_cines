"""FastAPI application entrypoint."""

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import limiter, router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Semantic AI Prompt Enhancer — preserve intent, improve specificity.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

_static_dir = Path(
    os.environ.get("STATIC_DIR", str(Path(__file__).resolve().parent.parent / "static"))
)
_has_spa = _static_dir.is_dir() and (_static_dir / "index.html").is_file()


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred. Please try again."},
    )


@app.get("/api")
async def api_root():
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/api/health",
        "enhance": "POST /api/enhance",
    }


if _has_spa:
    # Registered after API routes so /api and /docs stay on FastAPI.
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="frontend")
else:

    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "docs": "/docs",
            "health": "/api/health",
            "enhance": "POST /api/enhance",
        }
