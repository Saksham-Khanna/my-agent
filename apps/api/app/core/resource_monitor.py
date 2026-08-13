"""
Real resource readings for the Phase 9 GPU-aware scheduler.

The scheduler depends only on the ResourceMonitor abstraction defined here —
never on subprocesses or HTTP directly — so scheduling logic stays testable
with mocked ResourceSnapshot objects.

Two real sources are merged:
  - Ollama /api/ps  → which models are resident and their per-model size
  - nvidia-smi      → the actual GPU VRAM used/total (NVIDIA only)

faster-whisper runs on CPU (see ADR-010) and is deliberately excluded from
GPU VRAM accounting here; its footprint is tracked by the scheduler via
ModelDescriptor.estimated_ram_mb instead.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ResourceSnapshot:
    """Point-in-time resource readings for scheduling decisions."""

    vram_used_mb: Optional[float] = None
    vram_total_mb: Optional[float] = None
    models_loaded: List[dict] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ResourceMonitor:
    """Interface for snapshot sources. Tests substitute a fake."""

    async def snapshot(self) -> ResourceSnapshot:
        raise NotImplementedError


class OllamaResourceMonitor(ResourceMonitor):
    """Reads which models Ollama currently has resident via /api/ps."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 5.0):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.timeout = timeout

    async def snapshot(self) -> ResourceSnapshot:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/ps")
                response.raise_for_status()
                data = response.json()
            models = [
                {
                    "model": m.get("model"),
                    "size": m.get("size"),
                    "size_vram": m.get("size_vram"),
                }
                for m in data.get("models", [])
            ]
            vram_used = sum(
                m["size_vram"] for m in models if isinstance(m["size_vram"], (int, float))
            )
            return ResourceSnapshot(
                vram_used_mb=round(vram_used / (1024 * 1024), 2) if vram_used else None,
                vram_total_mb=None,
                models_loaded=models,
            )
        except Exception as e:  # noqa: BLE001 - degraded gracefully on any error
            logger.warning(f"Ollama /api/ps unavailable: {e}")
            return ResourceSnapshot()


class NvidiaSmiResourceMonitor(ResourceMonitor):
    """Reads real GPU VRAM usage via the nvidia-smi subprocess (NVIDIA only)."""

    def __init__(self, binary: Optional[str] = None, timeout: float = 5.0):
        self.binary = binary or shutil.which("nvidia-smi") or "nvidia-smi"
        self.timeout = timeout

    def _run_smi(self) -> Optional[ResourceSnapshot]:
        if not shutil.which(self.binary):
            return None
        try:
            proc = subprocess.run(
                [
                    self.binary,
                    "--query-gpu=memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            proc.check_returncode()
            line = proc.stdout.strip().splitlines()
            if not line:
                return None
            used, total = (float(part.strip()) for part in line[0].split(","))
            return ResourceSnapshot(vram_used_mb=used, vram_total_mb=total)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"nvidia-smi unavailable: {e}")
            return None

    async def snapshot(self) -> ResourceSnapshot:
        result = await asyncio.to_thread(self._run_smi)
        return result or ResourceSnapshot()


class CompositeResourceMonitor(ResourceMonitor):
    """Merges Ollama and nvidia-smi readings; prefers real GPU numbers."""

    def __init__(self, sources: List[ResourceMonitor]):
        self.sources = sources

    async def snapshot(self) -> ResourceSnapshot:
        results = await asyncio.gather(
            *(source.snapshot() for source in self.sources),
            return_exceptions=True,
        )
        merged = ResourceSnapshot()
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Resource monitor source failed: {result}")
                continue
            if result.vram_used_mb is not None:
                merged.vram_used_mb = result.vram_used_mb
            if result.vram_total_mb is not None:
                merged.vram_total_mb = result.vram_total_mb
            if result.models_loaded:
                merged.models_loaded.extend(result.models_loaded)
        return merged


def build_resource_monitor() -> ResourceMonitor:
    """Construct the default monitor stack (Ollama /api/ps + nvidia-smi)."""
    return CompositeResourceMonitor(
        sources=[
            OllamaResourceMonitor(),
            NvidiaSmiResourceMonitor(),
        ]
    )
