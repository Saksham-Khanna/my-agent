import time

import pytest

from app.core.resource_monitor import ResourceMonitor, ResourceSnapshot
from app.core.resource_scheduler import (
    ModelDescriptor,
    ModelRegistry,
    ResourceScheduler,
    build_default_registry,
)


class FakeMonitor(ResourceMonitor):
    def __init__(self, vram_used=None, vram_total=None):
        self._vram_used = vram_used
        self._vram_total = vram_total

    async def snapshot(self) -> ResourceSnapshot:
        return ResourceSnapshot(vram_used_mb=self._vram_used, vram_total_mb=self._vram_total)


class FakeProvider:
    """Provider that records lifecycle calls instead of touching hardware."""

    def __init__(self):
        self.load_calls = 0
        self.unload_calls = 0
        self.loaded = False

    async def load(self):
        self.load_calls += 1
        self.loaded = True

    async def unload(self):
        self.unload_calls += 1
        self.loaded = False

    def is_loaded(self):
        return self.loaded

    async def generate_stream(self, prompt):
        yield f"response to {prompt}"


def build_scheduler(
    profile="BALANCED",
    monitor=None,
    ram_enforcement=False,
    registry=None,
    on_update=None,
):
    return ResourceScheduler(
        monitor=monitor or FakeMonitor(),
        registry=registry or build_default_registry(),
        profile=profile,
        on_resource_update=on_update,
        enable_ram_enforcement=ram_enforcement,
    )


def fake_registry():
    registry = ModelRegistry()
    registry.register(ModelDescriptor(
        model_id="a", display_name="A", provider="fake", capability="llm",
        estimated_vram_mb=2000, estimated_ram_mb=500,
    ), FakeProvider())
    registry.register(ModelDescriptor(
        model_id="b", display_name="B", provider="fake", capability="vision",
        estimated_vram_mb=1500, estimated_ram_mb=500,
    ), FakeProvider())
    registry.register(ModelDescriptor(
        model_id="stt", display_name="STT", provider="fake", capability="stt",
        estimated_vram_mb=0, estimated_ram_mb=1000,
    ), FakeProvider())
    return registry


@pytest.mark.anyio
async def test_acquire_loads_and_tracks_active_requests():
    scheduler = build_scheduler(registry=fake_registry())
    async with scheduler.acquire("a") as provider:
        assert isinstance(provider, FakeProvider)
        descriptor, _ = scheduler.registry.get("a")
        assert descriptor.loaded is True
        assert descriptor.active_requests == 1
        assert provider.load_calls == 1
    assert descriptor.active_requests == 0


@pytest.mark.anyio
async def test_acquire_is_idempotent_for_loaded_model():
    scheduler = build_scheduler(registry=fake_registry())
    async with scheduler.acquire("a"):
        pass
    async with scheduler.acquire("a"):
        provider = scheduler.registry.get("a")[1]
        assert provider.load_calls == 1  # not re-loaded


@pytest.mark.anyio
async def test_acquire_unknown_model_raises():
    scheduler = build_scheduler(registry=fake_registry())
    with pytest.raises(KeyError):
        async with scheduler.acquire("does_not_exist"):
            pass


@pytest.mark.anyio
async def test_budget_evicts_lru_loaded_model():
    registry = fake_registry()
    scheduler = build_scheduler(registry=registry, profile="ECO")  # 2.5 GB budget

    async with scheduler.acquire("a"):  # 2.0 GB
        pass
    # Loading "b" (1.5 GB) would exceed 2.5 GB with "a" loaded -> evict "a".
    async with scheduler.acquire("b"):
        descriptor_a, provider_a = registry.get("a")
        descriptor_b, provider_b = registry.get("b")
        assert provider_a.unload_calls == 1
        assert descriptor_a.loaded is False
        assert descriptor_b.loaded is True


@pytest.mark.anyio
async def test_active_requests_prevent_eviction():
    registry = fake_registry()
    scheduler = build_scheduler(registry=registry, profile="ECO")

    async with scheduler.acquire("a"):
        # While "a" is in use, acquiring "b" should not evict "a".
        async with scheduler.acquire("b"):
            descriptor_a, _ = registry.get("a")
            assert descriptor_a.loaded is True


@pytest.mark.anyio
async def test_release_via_context_exit_decrements():
    scheduler = build_scheduler(registry=fake_registry())
    descriptor, _ = scheduler.registry.get("a")
    async with scheduler.acquire("a"):
        assert descriptor.active_requests == 1
    assert descriptor.active_requests == 0


@pytest.mark.anyio
async def test_idle_sweep_unloads_stale_models():
    registry = fake_registry()
    scheduler = build_scheduler(registry=registry, profile="BALANCED")
    scheduler.profile_config.idle_unload_seconds = 1

    async with scheduler.acquire("a"):
        pass
    # Model idle for longer than the timeout.
    descriptor_a, provider_a = registry.get("a")
    descriptor_a.last_used = time.time() - 10

    await scheduler.idle_sweep()

    assert descriptor_a.loaded is False
    assert provider_a.unload_calls == 1


@pytest.mark.anyio
async def test_idle_sweep_keeps_recent_models():
    registry = fake_registry()
    scheduler = build_scheduler(registry=registry, profile="BALANCED")
    scheduler.profile_config.idle_unload_seconds = 100

    async with scheduler.acquire("a"):
        pass

    await scheduler.idle_sweep()

    descriptor_a, provider_a = registry.get("a")
    assert descriptor_a.loaded is True
    assert provider_a.unload_calls == 0


@pytest.mark.anyio
async def test_idle_sweep_skips_active_models():
    registry = fake_registry()
    scheduler = build_scheduler(registry=registry, profile="ECO")
    scheduler.profile_config.idle_unload_seconds = 0  # always stale

    async with scheduler.acquire("a"):
        descriptor_a, provider_a = registry.get("a")
        descriptor_a.last_used = time.time() - 60
        await scheduler.idle_sweep()
        assert descriptor_a.loaded is True  # active request protects it
        assert provider_a.unload_calls == 0


@pytest.mark.anyio
async def test_set_profile_switches_budget_and_evicts():
    registry = fake_registry()
    scheduler = build_scheduler(registry=registry, profile="PERFORMANCE")

    async with scheduler.acquire("a"):  # 2.0 GB, fits in 4.5 GB
        pass
    async with scheduler.acquire("b"):  # +1.5 GB = 3.5 GB, still fits
        pass

    assert scheduler.profile == "PERFORMANCE"
    await scheduler.set_profile("ECO")  # 2.5 GB -> must evict one

    descriptor_a, provider_a = registry.get("a")
    descriptor_b, provider_b = registry.get("b")
    assert descriptor_a.loaded is not descriptor_b.loaded  # exactly one remains
    assert provider_a.unload_calls + provider_b.unload_calls == 1


@pytest.mark.anyio
async def test_set_profile_invalid_raises():
    scheduler = build_scheduler(registry=fake_registry())
    with pytest.raises(ValueError):
        await scheduler.set_profile("ULTRA")


@pytest.mark.anyio
async def test_snapshot_reports_real_monitor_numbers():
    scheduler = build_scheduler(
        registry=fake_registry(),
        monitor=FakeMonitor(vram_used=1234.0, vram_total=6144.0),
    )
    async with scheduler.acquire("stt"):  # CPU model, 0 VRAM
        pass
    snap = await scheduler.snapshot()
    assert snap["vram_used_mb"] == 1234.0
    assert snap["vram_budget_mb"] == 4096  # BALANCED 4.0 GB
    assert snap["ram_used_mb"] == 1000  # STT RAM tracked separately
    stt_model = next(m for m in snap["models"] if m["model_id"] == "stt")
    assert stt_model["estimated_vram_mb"] == 0
    assert stt_model["loaded"] is True


@pytest.mark.anyio
async def test_stt_excluded_from_vram_eviction():
    registry = fake_registry()
    scheduler = build_scheduler(registry=registry, profile="BALANCED")  # 4.0 GB

    async with scheduler.acquire("stt"):  # 0 VRAM, 1000 RAM
        pass
    async with scheduler.acquire("a"):  # 2.0 GB VRAM fits in 4.0 GB
        descriptor_stt, provider_stt = registry.get("stt")
        descriptor_a, provider_a = registry.get("a")
        assert descriptor_stt.loaded is True  # CPU model not evicted for VRAM
        assert provider_stt.unload_calls == 0
        assert descriptor_a.loaded is True


@pytest.mark.anyio
async def test_ram_enforcement_evicts_when_enabled():
    registry = fake_registry()
    scheduler = build_scheduler(registry=registry, profile="ECO", ram_enforcement=True)
    scheduler.profile_config.ram_budget_mb = 1200  # tiny RAM budget

    async with scheduler.acquire("stt"):  # 1000 MB RAM
        pass
    async with scheduler.acquire("a"):  # +500 MB RAM = 1500 > 1200 -> evict stt
        descriptor_stt, provider_stt = registry.get("stt")
        descriptor_a, _ = registry.get("a")
        assert provider_stt.unload_calls == 1
        assert descriptor_stt.loaded is False
        assert descriptor_a.loaded is True


@pytest.mark.anyio
async def test_resource_update_callback_fired_on_release():
    emitted = []
    scheduler = build_scheduler(
        registry=fake_registry(),
        on_update=lambda payload: emitted.append(payload),
    )
    async with scheduler.acquire("a"):
        pass
    assert len(emitted) == 1
    assert emitted[0]["profile"] == "BALANCED"


@pytest.mark.anyio
async def test_default_registry_contains_three_models():
    registry = build_default_registry()
    assert set(dict(registry.list()).keys()) == {"llm", "vision", "stt"}
