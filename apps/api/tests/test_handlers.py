import pytest
import asyncio
from app.core.models import TaskContext, TaskResult
from app.core.handlers import StubHandler
from app.core.state import OrbStateMachine, OrbState

@pytest.mark.anyio
async def test_stub_handler_returns_not_implemented():
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    ctx = TaskContext(mode="screen", text="hello", state_machine=state_machine)
    
    handler = StubHandler(mode_name="screen", required_phase=6)
    
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
    assert "Screen mode requires Phase 6" in result.message


@pytest.mark.anyio
async def test_vision_handler_no_image():
    from app.core.handlers import VisionHandler
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    ctx = TaskContext(mode="vision", text="hello", state_machine=state_machine)
    
    handler = VisionHandler()
    events = []
    async for event in handler.handle(ctx):
        events.append(event)
        
    assert events[0].current_state == OrbState.VISION
    assert events[1].current_state == OrbState.ERROR
    assert events[2].current_state == OrbState.IDLE
    assert events[-1].status == "failure"
    assert "No image provided" in events[-1].message


@pytest.mark.anyio
async def test_screen_handler_no_image():
    from app.core.handlers import ScreenHandler
    from app.core.models import TaskContext, TaskResult
    from app.core.state import OrbStateMachine, OrbState

    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    ctx = TaskContext(mode="screen", text="what do you see?", state_machine=state_machine)

    handler = ScreenHandler()
    events = []
    async for event in handler.handle(ctx):
        events.append(event)

    assert isinstance(events[0], tuple) and events[0][0] == "screen.capture_requested"
    result = events[-1]
    assert isinstance(result, TaskResult)
    assert result.status == "failure"
    assert "No screenshot provided" in result.message


@pytest.mark.anyio
async def test_vision_handler_emits_frame_analyzed(monkeypatch):
    from app.core.handlers import VisionHandler
    from app.core.models import TaskContext, TaskResult, Attachment
    from app.core.state import OrbStateMachine, OrbState

    class FakeVisionProvider:
        async def analyze(self, image_b64, prompt="Describe this image in detail."):
            return "a cat sitting on a table"

    monkeypatch.setattr("app.llm.vision_provider.VisionProvider", FakeVisionProvider)

    class FakeTalkHandler:
        async def handle(self, ctx):
            yield TaskResult(status="success", message="Response completed")

    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    image_att = Attachment(id="img_1", mime_type="image/png", data_b64="aW1hZ2VkYXRh")
    ctx = TaskContext(mode="vision", text="describe this", state_machine=state_machine, attachments=[image_att])

    handler = VisionHandler(talk_handler=FakeTalkHandler())
    events = []
    async for event in handler.handle(ctx):
        events.append(event)

    frame_events = [e for e in events if isinstance(e, tuple) and e[0] == "vision.frame_analyzed"]
    assert len(frame_events) == 1
    payload = frame_events[0][1]
    assert payload["description"] == "a cat sitting on a table"
    assert payload["attachment_id"] == "img_1"
    assert isinstance(events[-1], TaskResult)
    assert events[-1].status == "success"


@pytest.mark.anyio
async def test_memory_handler_store():
    from app.core.handlers import MemoryHandler
    from app.core.models import TaskContext, TaskResult
    from app.core.state import OrbStateMachine, OrbState
    from app.services.memory_store import MemoryStore
    from app.services.memory_service import MemoryService

    store = MemoryStore(db_path=":memory:")
    await store.initialize()
    svc = MemoryService(store=store)

    handler = MemoryHandler(memory_service=svc)
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    ctx = TaskContext(mode="memory", text="remember that my favorite color is blue", state_machine=state_machine)

    events = []
    async for event in handler.handle(ctx):
        events.append(event)

    result = events[-1]
    assert isinstance(result, TaskResult)
    assert result.status == "success"
    assert "Memory stored" in result.message

    results = await svc.recall("blue", limit=5)
    assert len(results) == 1
    assert "favorite color is blue" in results[0].content

    await store.close()


@pytest.mark.anyio
async def test_memory_handler_clear():
    from app.core.handlers import MemoryHandler
    from app.core.models import TaskContext, TaskResult
    from app.core.state import OrbStateMachine, OrbState
    from app.services.memory_store import MemoryStore
    from app.services.memory_service import MemoryService

    store = MemoryStore(db_path=":memory:")
    await store.initialize()
    svc = MemoryService(store=store)
    await svc.remember("test entry", source_mode="memory")

    handler = MemoryHandler(memory_service=svc)
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    ctx = TaskContext(mode="memory", text="clear all memories", state_machine=state_machine)

    events = []
    async for event in handler.handle(ctx):
        events.append(event)

    result = events[-1]
    assert isinstance(result, TaskResult)
    assert result.status == "success"
    assert "Cleared" in result.message
    assert "1" in result.message

    await store.close()
