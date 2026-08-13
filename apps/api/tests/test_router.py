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
async def test_router_dispatch_screen_mode_no_screenshot():
    router = TaskRouter()
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    ctx = TaskContext(mode="screen", text="what do you see?", state_machine=state_machine)
    
    events = []
    async for event in router.dispatch(ctx):
        events.append(event)
        
    assert events[0][0] == "task.started"
    assert events[1][0] == "screen.capture_requested"
    assert events[2][0] == "task.failed"
    assert "No screenshot provided" in events[2][1]["error"]

@pytest.mark.anyio
async def test_router_dispatch_vision_mode_no_image():
    router = TaskRouter()
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    ctx = TaskContext(mode="vision", text="describe this", state_machine=state_machine)
    
    events = []
    async for event in router.dispatch(ctx):
        events.append(event)
        
    assert events[0][0] == "task.started"
    assert isinstance(events[1], OrbStateEvent) and events[1].current_state == OrbState.VISION
    assert isinstance(events[2], OrbStateEvent) and events[2].current_state == OrbState.ERROR
    assert isinstance(events[3], OrbStateEvent) and events[3].current_state == OrbState.IDLE
    assert events[4][0] == "task.failed"
    assert "No image provided" in events[4][1]["error"]

@pytest.mark.anyio
async def test_router_memory_injection_in_talk_mode():
    from app.core.router import TaskRouter
    from app.core.models import TaskContext
    from app.core.state import OrbStateMachine, OrbState
    from app.services.memory_store import MemoryStore
    from app.services.memory_service import MemoryService

    store = MemoryStore(db_path=":memory:")
    await store.initialize()
    svc = MemoryService(store=store)
    await svc.remember("User likes Python programming", source_mode="talk")

    router = TaskRouter(memory_service=svc)
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    ctx = TaskContext(mode="talk", text="what do I like?", state_machine=state_machine)

    events = []
    async for event in router.dispatch(ctx):
        events.append(event)

    assert events[0][0] == "task.started"


@pytest.mark.anyio
async def test_router_no_memory_injection_in_actions():
    from app.core.router import TaskRouter
    from app.core.models import TaskContext
    from app.core.state import OrbStateMachine, OrbState

    router = TaskRouter()
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    ctx = TaskContext(mode="actions", text="system info", state_machine=state_machine)

    events = []
    async for event in router.dispatch(ctx):
        events.append(event)

    assert events[0][0] == "task.started"


@pytest.mark.anyio
async def test_router_screen_handler_replaces_stub():
    from app.core.router import TaskRouter
    from app.core.models import TaskContext
    from app.core.state import OrbStateMachine, OrbState

    router = TaskRouter()
    handler = router.handlers.get("screen")
    from app.core.handlers import ScreenHandler
    assert isinstance(handler, ScreenHandler)


@pytest.mark.anyio
async def test_router_memory_handler_replaces_stub():
    from app.core.router import TaskRouter
    from app.core.models import TaskContext
    from app.core.state import OrbStateMachine, OrbState

    router = TaskRouter()
    handler = router.handlers.get("memory")
    from app.core.handlers import MemoryHandler
    assert isinstance(handler, MemoryHandler)

