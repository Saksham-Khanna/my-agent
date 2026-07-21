import pytest
import asyncio
from app.core.models import TaskContext, TaskResult
from app.core.handlers import StubHandler
from app.core.state import OrbStateMachine, OrbState

@pytest.mark.anyio
async def test_stub_handler_returns_not_implemented():
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    ctx = TaskContext(mode="vision", text="hello", state_machine=state_machine)
    
    handler = StubHandler(mode_name="vision", required_phase=5)
    
    events = []
    async for event in handler.handle(ctx):
        events.append(event)
        
    assert len(events) == 4
    
    # Check states: THINKING -> ERROR -> IDLE
    assert events[0].current_state == OrbState.THINKING
    assert events[1].current_state == OrbState.ERROR
    assert events[2].current_state == OrbState.IDLE
    
    # Check result
    result = events[-1]
    assert isinstance(result, TaskResult)
    assert result.status == "not_implemented"
    assert "Vision mode requires Phase 5" in result.message
