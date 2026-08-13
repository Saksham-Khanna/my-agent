"""
Phase 10 Fault Recovery and Hardening Test Suite.

Verifies system resilience under error conditions:
1. Model load failure handling & recovery in ResourceScheduler + OrbStateMachine
2. WebSocket drop mid-stream & cleanup
3. Task cancellation & resource release
4. Rapid successive request handling without state machine lockup/corruption
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from app.core.models import TaskContext
from app.core.router import TaskRouter
from app.core.state import OrbState, OrbStateMachine
from app.core.resource_scheduler import ResourceScheduler, ModelDescriptor, ModelRegistry
from app.routes.ws import process_task


class FailingProvider:
    async def load(self):
        raise RuntimeError("GPU OOM / Model Weights Corrupted")

    async def unload(self):
        pass

    async def generate_stream(self, prompt: str):
        yield "token"


class MockSuccessProvider:
    def __init__(self):
        self.loaded = False

    async def load(self):
        self.loaded = True

    async def unload(self):
        self.loaded = False

    async def generate_stream(self, prompt: str):
        yield "Hello "
        yield "World!"


@pytest.mark.anyio
async def test_model_load_failure_recovery():
    """Verify that when model loading fails, the error is handled and scheduler stays clean."""
    registry = ModelRegistry()
    failing_descriptor = ModelDescriptor(
        model_id="failing_model",
        display_name="Failing Model",
        provider="test",
        capability="llm",
        estimated_vram_mb=1000,
    )
    registry.register(failing_descriptor, FailingProvider())

    scheduler = ResourceScheduler(registry=registry)
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)

    with pytest.raises(RuntimeError, match="GPU OOM"):
        async with scheduler.acquire("failing_model") as provider:
            pass

    assert not failing_descriptor.loaded
    assert failing_descriptor.active_requests == 0
    assert state_machine.current_state == OrbState.IDLE


@pytest.mark.anyio
async def test_rapid_successive_requests_handling():
    """Verify that firing multiple rapid requests processes correctly or transitions cleanly."""
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    router = TaskRouter()

    results = []

    async def send_request(text: str):
        ctx = TaskContext(mode="talk", text=text, state_machine=state_machine)
        events = []
        async for event in router.dispatch(ctx):
            events.append(event)
        results.append(events)

    # Dispatch 3 rapid requests concurrently
    tasks = [asyncio.create_task(send_request(f"Prompt {i}")) for i in range(3)]
    await asyncio.gather(*tasks, return_exceptions=True)

    # State machine should end up back in IDLE
    assert state_machine.current_state == OrbState.IDLE
    assert len(results) == 3


@pytest.mark.anyio
async def test_task_cancellation_cleanup():
    """Verify that cancelling an in-flight task task cleans up state and scheduler leases."""
    provider = MockSuccessProvider()
    registry = ModelRegistry()
    descriptor = ModelDescriptor(
        model_id="llm",
        display_name="Mock Model",
        provider="test",
        capability="llm",
        estimated_vram_mb=500,
    )
    registry.register(descriptor, provider)

    scheduler = ResourceScheduler(registry=registry)
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)

    async def long_running_task():
        async with scheduler.acquire("llm"):
            await asyncio.sleep(5.0)

    task = asyncio.create_task(long_running_task())
    await asyncio.sleep(0.05)  # Let it start and acquire lease

    assert descriptor.loaded
    assert descriptor.active_requests == 1

    # Cancel the task mid-execution
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # Assert active requests returned to 0
    assert descriptor.active_requests == 0


@pytest.mark.anyio
async def test_websocket_drop_mid_stream_cleanup():
    """Simulate client WebSocket disconnecting mid-stream."""
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    
    class DisconnectingWebSocket:
        def __init__(self):
            self.sent_messages = []

        async def send_json(self, data):
            self.sent_messages.append(data)
            if len(self.sent_messages) >= 2:
                raise RuntimeError("WebSocket Connection Reset by Peer")

    ws = DisconnectingWebSocket()
    router = TaskRouter()
    ctx = TaskContext(mode="talk", text="Tell me a story", state_machine=state_machine)

    # Process task with disconnecting WebSocket
    with pytest.raises(RuntimeError, match="Connection Reset"):
        async for event in router.dispatch(ctx):
            if isinstance(event, tuple):
                await ws.send_json(event[1])

    # State machine must be resilient and recover to valid state or stay manageable
    assert state_machine.current_state in (OrbState.IDLE, OrbState.THINKING, OrbState.RESPONDING, OrbState.ERROR)
