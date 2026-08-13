from unittest.mock import AsyncMock, patch

import pytest
from app.llm.vision_provider import VisionProvider


@pytest.mark.anyio
async def test_vision_provider_load_pins_model():
    provider = VisionProvider(base_url="http://test", model="test-vision")

    mock_response = AsyncMock()
    mock_response.raise_for_status = AsyncMock()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__.return_value = mock_client
    with patch("httpx.AsyncClient", return_value=mock_client_cm):
        await provider.load()

    assert provider.is_loaded() is True
    mock_client.post.assert_called_once_with(
        "http://test/api/generate",
        json={"model": "test-vision", "prompt": "", "stream": False, "keep_alive": "-1"},
        timeout=60.0,
    )


@pytest.mark.anyio
async def test_vision_provider_unload_releases_model():
    provider = VisionProvider(base_url="http://test", model="test-vision")

    mock_response = AsyncMock()
    mock_response.raise_for_status = AsyncMock()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__.return_value = mock_client
    with patch("httpx.AsyncClient", return_value=mock_client_cm):
        await provider.load()
        await provider.unload()

    assert provider.is_loaded() is False
    unload_call = mock_client.post.call_args_list[1]
    assert unload_call.kwargs["json"]["keep_alive"] == "0"
