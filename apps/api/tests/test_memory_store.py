import pytest
from pathlib import Path
from app.services.memory_store import MemoryStore, MemoryEntry


@pytest.mark.anyio
async def test_memory_store_crud(tmp_path: Path):
    db_file = str(tmp_path / "test_memory.db")
    store = MemoryStore(db_path=db_file)
    await store.initialize()

    entry = MemoryEntry(
        content="My favorite color is blue",
        session_id="session_1",
        source_mode="memory"
    )
    entry_id = await store.store(entry)
    assert entry_id is not None

    fetched = await store.get_by_id(entry_id)
    assert fetched is not None
    assert fetched.content == "My favorite color is blue"
    assert fetched.session_id == "session_1"
    assert fetched.source_mode == "memory"

    await store.close()


@pytest.mark.anyio
async def test_memory_store_search(tmp_path: Path):
    db_file = str(tmp_path / "test_search.db")
    store = MemoryStore(db_path=db_file)
    await store.initialize()

    await store.store(MemoryEntry(content="The sky is blue", session_id="s1"))
    await store.store(MemoryEntry(content="Grass is green", session_id="s1"))
    await store.store(MemoryEntry(content="Ocean is deep blue", session_id="s1"))

    results = await store.search("blue", limit=5)
    assert len(results) == 2
    assert all("blue" in r.content for r in results)

    no_results = await store.search("nonexistent_term_xyz", limit=5)
    assert len(no_results) == 0

    await store.close()


@pytest.mark.anyio
async def test_memory_store_clear_all(tmp_path: Path):
    db_file = str(tmp_path / "test_clear.db")
    store = MemoryStore(db_path=db_file)
    await store.initialize()

    await store.store(MemoryEntry(content="Entry 1", session_id="s1"))
    await store.store(MemoryEntry(content="Entry 2", session_id="s1"))

    stats = await store.get_stats()
    assert stats["total"] == 2

    count = await store.clear_all()
    assert count == 2

    stats = await store.get_stats()
    assert stats["total"] == 0

    await store.close()


@pytest.mark.anyio
async def test_memory_store_get_stats(tmp_path: Path):
    db_file = str(tmp_path / "test_stats.db")
    store = MemoryStore(db_path=db_file)
    await store.initialize()

    stats = await store.get_stats()
    assert stats["total"] == 0
    assert stats["oldest"] is None
    assert stats["newest"] is None

    await store.store(MemoryEntry(content="Entry 1", session_id="s1"))
    stats = await store.get_stats()
    assert stats["total"] == 1
    assert stats["oldest"] is not None
    assert stats["newest"] is not None

    await store.close()


@pytest.mark.anyio
async def test_memory_store_get_recent(tmp_path: Path):
    db_file = str(tmp_path / "test_recent.db")
    store = MemoryStore(db_path=db_file)
    await store.initialize()

    for i in range(5):
        await store.store(MemoryEntry(content=f"Entry {i}", session_id="s1"))

    recent = await store.get_recent(limit=3)
    assert len(recent) == 3
    assert recent[0].content == "Entry 4"

    await store.close()
