"""
Spectra API — Phase 0 entrypoint.

Run with:
    uvicorn app.main:app --reload --port 8000

Scope (Phase 0 only):
    - GET /health
    - WS   /ws        (connection handshake + ping/pong)

Explicitly out of scope for this phase: LLM integration, Ollama, Whisper,
vision models, RAG, embeddings, vector databases, memory, tool execution,
LangGraph, GPU scheduling. See docs/DEVELOPMENT_PHASES.md.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes import health, ws

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Local-first desktop AI agent — Phase 0 foundation backend.",
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
