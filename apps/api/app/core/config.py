"""
Application configuration for the Spectra backend.

All phases are implemented — settings cover LLM, STT, vision, file
intelligence, memory, and GPU-aware scheduling. See docs/DECISIONS.md
for each configuration choice.
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
    app_version: str = "1.0.0"
    environment: str = "development"

    # Network
    # 127.0.0.1 only â€” Phase 0 has no reason to bind 0.0.0.0.
    host: str = "127.0.0.1"
    port: int = 8000

    # CORS / allowed origins for the Tauri dev server (Vite default port).
    allowed_origins: list[str] = [
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "tauri://localhost",
    ]

    # Resource posture. Read by the Phase 9 GPU-aware scheduler to decide
    # which models may stay loaded and when to unload them.
    power_profile: str = "BALANCED"  # ECO | BALANCED | PERFORMANCE
    max_vram_budget_gb: float = 4.5
    max_ram_budget_gb: float = 10.0

    # Phase 9: per-profile VRAM budgets (GB) and idle-unload timeouts (s).
    eco_vram_budget_gb: float = 2.5
    balanced_vram_budget_gb: float = 4.0
    performance_vram_budget_gb: float = 4.5
    eco_idle_unload_seconds: int = 30
    balanced_idle_unload_seconds: int = 120
    performance_idle_unload_seconds: int = 600

    # Phase 9: enforce the RAM budget in addition to VRAM. Off by default;
    # the scheduler always tracks and reports RAM, but only evicts for RAM
    # pressure when this is enabled.
    enable_ram_budget_enforcement: bool = False

    # Phase 1: Local LLM Configuration
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:3b"

    # Phase 4: Local STT Configuration
    stt_model: str = "tiny.en"

    # Phase 5: Local Vision Configuration
    vision_model: str = "moondream"

    # Phase 6: File Intelligence Configuration
    sqlite_db_path: str = "spectra_files.db"
    index_target_dir: str = "docs"

    # Phase 8: Memory Configuration
    memory_db_path: str = "spectra_memory.db"


settings = Settings()

