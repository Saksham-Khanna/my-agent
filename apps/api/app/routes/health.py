"""Health endpoint — used by the desktop app and by developers to verify
that the backend process is alive. No dependency on any AI subsystem."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "phase": "0-foundation",
    }
