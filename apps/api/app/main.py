"""
Spectra API — application entrypoint.

Run with:
    uvicorn app.main:app --reload --port 8000

Endpoints:
    - GET  /health    Health check
    - WS   /ws        Agent communication (state, tasks, streaming)

See docs/DEVELOPMENT_PHASES.md for the full build history.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes import health, ws

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Spectra — local-first desktop AI agent backend.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ws.router)


@app.get("/")
async def root() -> dict:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "websocket": "/ws",
    }

