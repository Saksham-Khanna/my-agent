"""
Phase 9 — GPU-aware model scheduler.

The ResourceScheduler is the single authority for when local AI models
(LLM, vision, STT) are loaded or unloaded. Providers perform inference;
the scheduler decides residency based on the active power profile, recent
usage, and the VRAM/RAM budgets read from the ResourceMonitor.

Usage:
    scheduler = build_default_scheduler()
    await scheduler.start()
    async with scheduler.acquire("llm") as provider:
        async for token in provider.generate_stream(prompt):
            ...
"""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.core.power_profiles import (
    DEFAULT_PROFILE,
    PROFILE_CONFIGS,
    PowerProfileConfig,
    get_profile_config,
)
from app.core.resource_monitor import ResourceMonitor, build_resource_monitor
from app.llm.ollama_provider import OllamaProvider
from app.llm.stt_provider import STTProvider
from app.llm.vision_provider import VisionProvider

logger = logging.getLogger(__name__)

ModelEntry = Tuple["ModelDescriptor", Any]


@dataclass
class ModelDescriptor:
    """Generic, provider-agnostic description of a schedulable model."""

    model_id: str
    display_name: str
    provider: str
    capability: str  # "llm" | "vision" | "stt"
    estimated_vram_mb: int
    estimated_ram_mb: int = 0
    loaded: bool = False
    last_used: float = field(default_factory=time.time)
    loading: bool = False
    active_requests: int = 0


class ModelRegistry:
    """Registry of schedulable models keyed by model_id."""

    def __init__(self) -> None:
        self._models: Dict[str, ModelEntry] = {}

    def register(self, descriptor: ModelDescriptor, provider: Any) -> None:
        self._models[descriptor.model_id] = (descriptor, provider)

    def get(self, model_id: str) -> Optional[ModelEntry]:
        return self._models.get(model_id)

    def list(self) -> List[Tuple[str, ModelEntry]]:
        return list(self._models.items())


def build_default_registry() -> ModelRegistry:
    """Register the three local models the scheduler manages."""
    registry = ModelRegistry()
    registry.register(
        ModelDescriptor(
            model_id="llm",
            display_name="Qwen2.5 3B",
            provider="ollama",
            capability="llm",
            estimated_vram_mb=2300,
            estimated_ram_mb=500,
        ),
        OllamaProvider(),
    )
    registry.register(
        ModelDescriptor(
            model_id="vision",
            display_name="moondream",
            provider="ollama",
            capability="vision",
            estimated_vram_mb=1500,
            estimated_ram_mb=500,
        ),
        VisionProvider(),
    )
    registry.register(
        ModelDescriptor(
            model_id="stt",
            display_name="faster-whisper tiny.en",
            provider="faster-whisper",
            capability="stt",
            estimated_vram_mb=0,  # CPU-resident per ADR-010
            estimated_ram_mb=1000,
        ),
        STTProvider(),
    )
    return registry


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


class ResourceScheduler:
    """
    Central authority for model lifecycle. Loads on acquire, evicts the
    least-recently-used idle models when a budget would be exceeded, and
    unloads idle models according to the active power profile.
    """

    def __init__(
        self,
        monitor: Optional[ResourceMonitor] = None,
        registry: Optional[ModelRegistry] = None,
        profile: str = DEFAULT_PROFILE,
        on_resource_update=None,
        enable_ram_enforcement: bool = False,
    ):
        self.monitor = monitor or build_resource_monitor()
        self.registry = registry or build_default_registry()
        self.on_resource_update = on_resource_update
        self.enable_ram_enforcement = enable_ram_enforcement
        self._profile = profile.upper()
        self._profile_config: PowerProfileConfig = replace(get_profile_config(self._profile))
        self._load_locks: Dict[str, asyncio.Lock] = {
            model_id: asyncio.Lock() for model_id, _ in self.registry.list()
        }
        self._background_task: Optional[asyncio.Task] = None

    @property
    def profile(self) -> str:
        return self._profile

    @property
    def profile_config(self) -> PowerProfileConfig:
        return self._profile_config

    async def set_profile(self, name: str) -> None:
        """Switch the active profile at runtime (no restart needed)."""
        normalized = name.upper()
        if normalized not in PROFILE_CONFIGS:
            raise ValueError(f"Unknown power profile: {name}")
        if normalized == self._profile:
            return
        logger.info(f"Switching power profile: {self._profile} -> {normalized}")
        self._profile = normalized
        self._profile_config = replace(get_profile_config(normalized))
        await self._enforce_current_budget()
        await self._emit_resource_update()

    @asynccontextmanager
    async def acquire(self, model_id: str):
        """
        Lease a loaded provider. Loads the model if needed (evicting LRU
        models to fit the budget), tracks active requests and last use,
        and releases the lease on exit.
        """
        entry = self.registry.get(model_id)
        if entry is None:
            raise KeyError(f"Unknown model: {model_id}")
        descriptor, provider = entry

        lock = self._load_locks[model_id]
        async with lock:
            if not descriptor.loaded:
                if self._profile_config.aggressive_unload:
                    await self._evict_all_idle(except_model_id=model_id)
                else:
                    await self._evict_for(
                        descriptor.estimated_vram_mb, descriptor.estimated_ram_mb
                    )
                await provider.load()
                descriptor.loaded = True
                logger.info(f"Loaded model: {model_id}")
            descriptor.active_requests += 1
            descriptor.last_used = time.time()

        try:
            yield provider
        finally:
            descriptor.active_requests -= 1
            descriptor.last_used = time.time()
            await self._emit_resource_update()

    async def unload(self, model_id: str) -> None:
        entry = self.registry.get(model_id)
        if entry is None:
            return
        descriptor, provider = entry
        if not descriptor.loaded:
            return
        descriptor.loading = True
        try:
            await provider.unload()
        finally:
            descriptor.loading = False
            descriptor.loaded = False
            logger.info(f"Unloaded model: {model_id}")

    async def idle_sweep(self) -> None:
        """Unload models idle longer than the profile's timeout."""
        config = self._profile_config
        now = time.time()
        for model_id, (descriptor, _) in self.registry.list():
            if not descriptor.loaded or descriptor.active_requests > 0 or descriptor.loading:
                continue
            idle_seconds = now - descriptor.last_used
            if idle_seconds >= config.idle_unload_seconds:
                await self.unload(model_id)

    async def snapshot(self) -> Dict[str, Any]:
        """Payload for the system.resource_update event."""
        monitor_snap = await self.monitor.snapshot()
        config = self._profile_config
        vram_used = sum(d.estimated_vram_mb for _, (d, _) in self.registry.list() if d.loaded)
        ram_used = sum(d.estimated_ram_mb for _, (d, _) in self.registry.list() if d.loaded)
        return {
            "profile": self._profile,
            "vram_used_mb": monitor_snap.vram_used_mb if monitor_snap.vram_used_mb is not None else vram_used,
            "vram_budget_mb": config.vram_budget_mb,
            "ram_used_mb": ram_used,
            "ram_budget_mb": config.ram_budget_mb,
            "models": [
                {
                    "model_id": model_id,
                    "display_name": d.display_name,
                    "provider": d.provider,
                    "capability": d.capability,
                    "loaded": d.loaded,
                    "estimated_vram_mb": d.estimated_vram_mb,
                    "estimated_ram_mb": d.estimated_ram_mb,
                    "last_used": _iso(d.last_used),
                    "active_requests": d.active_requests,
                }
                for model_id, (d, _) in self.registry.list()
            ],
        }

    def _loaded_vram(self) -> int:
        return sum(d.estimated_vram_mb for _, (d, _) in self.registry.list() if d.loaded)

    def _loaded_ram(self) -> int:
        return sum(d.estimated_ram_mb for _, (d, _) in self.registry.list() if d.loaded)

    async def _evict_for(self, vram_needed: int, ram_needed: int) -> None:
        """Evict LRU idle models until the profile budget fits the new load."""
        while True:
            vram_ok = self._loaded_vram() + vram_needed <= self._profile_config.vram_budget_mb
            ram_ok = (not self.enable_ram_enforcement) or (
                self._loaded_ram() + ram_needed <= self._profile_config.ram_budget_mb
            )
            if vram_ok and ram_ok:
                return
            candidate = self._next_eviction_candidate()
            if candidate is None:
                logger.warning(
                    f"Cannot fit model within budget (vram_needed={vram_needed}mb); "
                    f"all loaded models have active requests."
                )
                return
            await self.unload(candidate)

    async def _enforce_current_budget(self) -> None:
        """Evict LRU idle models until the current loads fit the budget."""
        while self._loaded_vram() > self._profile_config.vram_budget_mb:
            candidate = self._next_eviction_candidate()
            if candidate is None:
                return
            await self.unload(candidate)
        if self.enable_ram_enforcement:
            while self._loaded_ram() > self._profile_config.ram_budget_mb:
                candidate = self._next_eviction_candidate()
                if candidate is None:
                    return
                await self.unload(candidate)

    async def _evict_all_idle(self, except_model_id: Optional[str] = None) -> None:
        """Aggressive profiles keep at most one model warm."""
        for model_id, (descriptor, _) in self.registry.list():
            if descriptor.loaded and descriptor.active_requests == 0 and model_id != except_model_id:
                await self.unload(model_id)

    def _next_eviction_candidate(self) -> Optional[str]:
        """LRU idle loaded model, or None if every loaded model is in use."""
        candidates = [
            (model_id, d)
            for model_id, (d, _) in self.registry.list()
            if d.loaded and d.active_requests == 0 and not d.loading
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda e: e[1].last_used)
        return candidates[0][0]

    async def _emit_resource_update(self) -> None:
        if self.on_resource_update is None:
            return
        try:
            payload = await self.snapshot()
            await self.on_resource_update(payload)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to emit system.resource_update")

    def start(self, interval: float = 15.0) -> None:
        """Start the periodic idle-sweep + reporting loop."""
        if self._background_task is not None:
            return

        async def _loop():
            while True:
                await asyncio.sleep(interval)
                try:
                    await self.idle_sweep()
                    await self._emit_resource_update()
                except asyncio.CancelledError:
                    raise
                except Exception:  # noqa: BLE001
                    logger.exception("Resource scheduler loop error")

        self._background_task = asyncio.create_task(_loop())

    async def stop(self) -> None:
        if self._background_task is not None:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
            self._background_task = None


def build_default_scheduler(
    monitor: Optional[ResourceMonitor] = None,
    on_resource_update=None,
    enable_ram_enforcement: bool = False,
) -> ResourceScheduler:
    """Construct the default scheduler wired to the default registry/monitor."""
    from app.core.config import settings

    return ResourceScheduler(
        monitor=monitor or build_resource_monitor(),
        registry=build_default_registry(),
        profile=settings.power_profile,
        on_resource_update=on_resource_update,
        enable_ram_enforcement=settings.enable_ram_budget_enforcement
        or enable_ram_enforcement,
    )
