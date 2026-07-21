"""
Application configuration for the Spectra backend.

Phase 0 scope: only the settings needed to run a health endpoint and a
WebSocket handshake. Do not add model paths, GPU settings, or provider
API keys here until the phase that actually needs them (see
docs/DEVELOPMENT_PHASES.md).
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SPECTRA_",
        extra="ignore",
    )

    # Identity
    app_name: str = "Spectra API"
    app_version: str = "0.1.0"
    environment: str = "development"

    # Network
    # 127.0.0.1 only — Phase 0 has no reason to bind 0.0.0.0.
    host: str = "127.0.0.1"
    port: int = 8000

    # CORS / allowed origins for the Tauri dev server (Vite default port).
    allowed_origins: list[str] = [
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "tauri://localhost",
    ]

    # Resource posture (informational only in Phase 0 — no model runs yet).
    # Values are placeholders that future phases (see Phase 9, GPU-aware
    # scheduler) will read to decide how much work the agent may do.
    power_profile: str = "BALANCED"  # ECO | BALANCED | PERFORMANCE
    max_vram_budget_gb: float = 4.5
    max_ram_budget_gb: float = 10.0

    # Phase 1: Local LLM Configuration
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:4b"


settings = Settings()
