import pytest
import asyncio
from app.core.models import TaskContext
from app.core.router import TaskRouter
from app.core.state import OrbStateMachine, OrbState, OrbStateEvent

@pytest.mark.anyio
async def test_router_dispatch_unknown_mode():
    router = TaskRouter()
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    ctx = TaskContext(mode="unknown_mode", text="test", state_machine=state_machine)
    
    events = []
    async for event in router.dispatch(ctx):
        events.append(event)
        
    assert len(events) == 2
    assert events[0][0] == "task.started"
    assert events[1][0] == "task.failed"
    assert "Unknown mode: unknown_mode" in events[1][1]["error"]

@pytest.mark.anyio
async def test_router_dispatch_stub_mode():
    router = TaskRouter()
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    ctx = TaskContext(mode="vision", text="what do you see?", state_machine=state_machine)
    
    events = []
    async for event in router.dispatch(ctx):
        events.append(event)
        
    # Expected events:
    # 1. task.started
    # 2. OrbStateEvent (THINKING)
    # 3. OrbStateEvent (ERROR)
    # 4. OrbStateEvent (IDLE)
    # 5. task.failed (since status is not_implemented, the router maps it to task.failed)
    
    assert events[0][0] == "task.started"
    assert isinstance(events[1], OrbStateEvent) and events[1].current_state == OrbState.THINKING
    assert isinstance(events[2], OrbStateEvent) and events[2].current_state == OrbState.ERROR
    assert isinstance(events[3], OrbStateEvent) and events[3].current_state == OrbState.IDLE
    assert events[4][0] == "task.failed"
    assert events[4][1]["status"] == "not_implemented"
