from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.llm.ollama_provider import OllamaProvider


@pytest.mark.anyio
async def test_ollama_provider_streams_tokens():
    provider = OllamaProvider(base_url="http://test", model="test-model")
    
    # Create an async generator for mock response aiter_lines
    async def mock_aiter_lines():
        yield b'{"response": "Hello"}\n'
        yield b'{"response": " world"}\n'
        yield b'{"response": "!", "done": true}\n'

    mock_response = AsyncMock()
    mock_response.aiter_lines = mock_aiter_lines
    mock_response.raise_for_status = AsyncMock()
    
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_response

    mock_client = AsyncMock()
    mock_client.stream = MagicMock(return_value=mock_context_manager)

    # Patch httpx.AsyncClient
    with patch("httpx.AsyncClient", return_value=mock_client) as mock_client_class:
        # We need to make the context manager of AsyncClient itself work
        mock_client_class_cm = AsyncMock()
        mock_client_class_cm.__aenter__.return_value = mock_client
        mock_client_class.return_value = mock_client_class_cm

        tokens = []
        async for token in provider.generate_stream("Say hello"):
            tokens.append(token)

        assert tokens == ["Hello", " world", "!"]
        
        # Verify calls
        mock_client.stream.assert_called_once_with(
            "POST", 
            "http://test/api/generate", 
            json={"model": "test-model", "prompt": "Say hello", "stream": True},
            timeout=None
        )


@pytest.mark.anyio
async def test_ollama_provider_load_pins_model():
    provider = OllamaProvider(base_url="http://test", model="test-model")

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
        json={"model": "test-model", "prompt": "", "stream": False, "keep_alive": "-1"},
        timeout=60.0,
    )


@pytest.mark.anyio
async def test_ollama_provider_unload_releases_model():
    provider = OllamaProvider(base_url="http://test", model="test-model")

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


@pytest.mark.anyio
async def test_ollama_provider_load_is_idempotent():
    provider = OllamaProvider(base_url="http://test", model="test-model")
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=AsyncMock(raise_for_status=AsyncMock()))
    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__.return_value = mock_client
    with patch("httpx.AsyncClient", return_value=mock_client_cm):
        await provider.load()
        await provider.load()
    assert mock_client.post.call_count == 1


@pytest.mark.anyio
async def test_ollama_provider_unload_is_idempotent():
    provider = OllamaProvider(base_url="http://test", model="test-model")
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=AsyncMock(raise_for_status=AsyncMock()))
    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__.return_value = mock_client
    with patch("httpx.AsyncClient", return_value=mock_client_cm):
        await provider.load()
        await provider.unload()
        await provider.unload()
    assert mock_client.post.call_count == 2  # load + one unload
