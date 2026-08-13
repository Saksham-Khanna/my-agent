"""Health endpoint — used by the desktop app and by developers to verify
that the backend process is alive. No dependency on any AI subsystem."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])

_STARTUP_TIME = datetime.now(timezone.utc).isoformat()


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "phase": "10-polish",
        "started_at": _STARTUP_TIME,
    }
