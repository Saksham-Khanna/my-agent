import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.resource_monitor import (
    CompositeResourceMonitor,
    NvidiaSmiResourceMonitor,
    OllamaResourceMonitor,
    ResourceSnapshot,
)


@pytest.mark.anyio
async def test_ollama_monitor_parses_ps():
    monitor = OllamaResourceMonitor(base_url="http://test", timeout=1.0)
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "models": [
            {"model": "qwen2.5:3b", "size": 2100000000, "size_vram": 2300000000},
            {"model": "moondream", "size": 1200000000, "size_vram": 1500000000},
        ]
    })

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__.return_value = mock_client
    with patch("httpx.AsyncClient", return_value=mock_client_cm):
        snapshot = await monitor.snapshot()

    assert snapshot.vram_used_mb == pytest.approx((2300000000 + 1500000000) / (1024 * 1024))
    assert len(snapshot.models_loaded) == 2
    assert snapshot.models_loaded[0]["model"] == "qwen2.5:3b"


@pytest.mark.anyio
async def test_ollama_monitor_graceful_on_error():
    monitor = OllamaResourceMonitor(base_url="http://unreachable", timeout=0.1)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=Exception("connection refused"))
    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__.return_value = mock_client
    with patch("httpx.AsyncClient", return_value=mock_client_cm):
        snapshot = await monitor.snapshot()

    assert snapshot.vram_used_mb is None
    assert snapshot.models_loaded == []


@pytest.mark.anyio
async def test_nvidia_smi_monitor_parses_output():
    monitor = NvidiaSmiResourceMonitor(binary="nvidia-smi", timeout=1.0)
    monitor._run_smi = MagicMock(
        return_value=ResourceSnapshot(vram_used_mb=1234.0, vram_total_mb=6144.0)
    )
    snapshot = await monitor.snapshot()
    assert snapshot.vram_used_mb == 1234.0
    assert snapshot.vram_total_mb == 6144.0


@pytest.mark.anyio
async def test_nvidia_smi_monitor_graceful_when_absent():
    monitor = NvidiaSmiResourceMonitor(binary="definitely-not-a-gpu-tool", timeout=1.0)
    monitor._run_smi = MagicMock(return_value=None)
    snapshot = await monitor.snapshot()
    assert snapshot.vram_used_mb is None


@pytest.mark.anyio
async def test_composite_monitor_merges_sources():
    ollama = AsyncMock()
    ollama.snapshot.return_value = ResourceSnapshot(
        models_loaded=[{"model": "qwen2.5:3b"}]
    )
    smi = AsyncMock()
    smi.snapshot.return_value = ResourceSnapshot(vram_used_mb=3000.0, vram_total_mb=6144.0)

    monitor = CompositeResourceMonitor(sources=[ollama, smi])
    snapshot = await monitor.snapshot()

    assert snapshot.vram_used_mb == 3000.0
    assert snapshot.vram_total_mb == 6144.0
    assert len(snapshot.models_loaded) == 1


@pytest.mark.anyio
async def test_composite_monitor_skips_failed_sources():
    failed = AsyncMock()
    failed.snapshot.side_effect = Exception("boom")
    smi = AsyncMock()
    smi.snapshot.return_value = ResourceSnapshot(vram_used_mb=2500.0, vram_total_mb=6144.0)

    monitor = CompositeResourceMonitor(sources=[failed, smi])
    snapshot = await monitor.snapshot()

    assert snapshot.vram_used_mb == 2500.0
