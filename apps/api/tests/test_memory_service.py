import pytest
from app.services.memory_store import MemoryStore
from app.services.memory_service import MemoryService


class CallbackRecorder:
    def __init__(self):
        self.calls = []

    async def __call__(self, payload: dict):
        self.calls.append(payload)


@pytest.mark.anyio
async def test_memory_service_remember_and_recall(tmp_path):
    store = MemoryStore(db_path=str(tmp_path / "test_svc.db"))
    await store.initialize()
    cb = CallbackRecorder()
    svc = MemoryService(store=store, on_updated=cb)

    entry_id = await svc.remember("My name is Alice", source_mode="memory")
    assert entry_id is not None
    assert len(cb.calls) == 1
    assert cb.calls[0]["action"] == "stored"

    results = await svc.recall("Alice", limit=5)
    assert len(results) == 1
    assert results[0].content == "My name is Alice"

    await store.close()


@pytest.mark.anyio
async def test_memory_service_get_memory_context(tmp_path):
    store = MemoryStore(db_path=str(tmp_path / "test_ctx.db"))
    await store.initialize()
    svc = MemoryService(store=store)

    context = await svc.get_memory_context("nonexistent")
    assert context == ""

    await svc.remember("User likes Python", source_mode="talk")
    context = await svc.get_memory_context("Python", max_tokens=2000)
    assert "[Relevant Memories]" in context
    assert "Python" in context

    await store.close()


@pytest.mark.anyio
async def test_memory_service_forget_all(tmp_path):
    store = MemoryStore(db_path=str(tmp_path / "test_forget.db"))
    await store.initialize()
    cb = CallbackRecorder()
    svc = MemoryService(store=store, on_updated=cb)

    await svc.remember("Entry 1", source_mode="memory")
    await svc.remember("Entry 2", source_mode="memory")

    count = await svc.forget_all()
    assert count == 2
    assert len(cb.calls) == 3
    assert cb.calls[-1]["action"] == "cleared"
    assert cb.calls[-1]["count"] == 2

    results = await svc.recall("Entry", limit=5)
    assert len(results) == 0

    await store.close()


@pytest.mark.anyio
async def test_memory_service_list_memories(tmp_path):
    store = MemoryStore(db_path=str(tmp_path / "test_list.db"))
    await store.initialize()
    svc = MemoryService(store=store)

    for i in range(3):
        await svc.remember(f"Memory {i}", source_mode="memory")

    entries = await svc.list_memories(limit=10)
    assert len(entries) == 3

    await store.close()
