"""
Power profile definitions for the Phase 9 GPU-aware model scheduler.

Each profile configures how aggressively the scheduler unloads models and
how much VRAM (and optionally RAM) it may use. The active profile is
runtime-switchable without restarting the app (see ResourceScheduler).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.core.config import settings


class PowerProfile(str, Enum):
    ECO = "ECO"
    BALANCED = "BALANCED"
    PERFORMANCE = "PERFORMANCE"


@dataclass
class PowerProfileConfig:
    """Tuning knobs for one power profile."""

    vram_budget_mb: int
    ram_budget_mb: int
    idle_unload_seconds: int
    aggressive_unload: bool


def _gb_to_mb(gb: float) -> int:
    return int(gb * 1024)


def build_profile_configs() -> dict[str, PowerProfileConfig]:
    """Build profile configs from settings so env vars stay the source of truth."""
    return {
        PowerProfile.ECO.value: PowerProfileConfig(
            vram_budget_mb=_gb_to_mb(settings.eco_vram_budget_gb),
            ram_budget_mb=_gb_to_mb(settings.max_ram_budget_gb),
            idle_unload_seconds=settings.eco_idle_unload_seconds,
            aggressive_unload=True,
        ),
        PowerProfile.BALANCED.value: PowerProfileConfig(
            vram_budget_mb=_gb_to_mb(settings.balanced_vram_budget_gb),
            ram_budget_mb=_gb_to_mb(settings.max_ram_budget_gb),
            idle_unload_seconds=settings.balanced_idle_unload_seconds,
            aggressive_unload=False,
        ),
        PowerProfile.PERFORMANCE.value: PowerProfileConfig(
            vram_budget_mb=_gb_to_mb(settings.performance_vram_budget_gb),
            ram_budget_mb=_gb_to_mb(settings.max_ram_budget_gb),
            idle_unload_seconds=settings.performance_idle_unload_seconds,
            aggressive_unload=False,
        ),
    }


# Default profile (BALANCED) and the full mapping.
DEFAULT_PROFILE = PowerProfile.BALANCED.value
PROFILE_CONFIGS: dict[str, PowerProfileConfig] = build_profile_configs()


def get_profile_config(name: str) -> PowerProfileConfig:
    """Return the config for a profile name, falling back to BALANCED."""
    return PROFILE_CONFIGS.get(name, PROFILE_CONFIGS[DEFAULT_PROFILE])
