import pytest
import asyncio
from pathlib import Path
from app.services.file_index import FileIndex
from app.services.indexer import FileIndexer
from app.core.models import TaskContext, Attachment, AttachmentStorage
from app.core.state import OrbStateMachine, OrbState
from app.core.handlers import FilesHandler, BaseHandler, TaskResult

class MockTalkHandler(BaseHandler):
    def __init__(self):
        self.received_prompt = ""

    async def handle(self, ctx: TaskContext):
        self.received_prompt = ctx.text
        yield TaskResult(status="success", message="Mock response completed")

@pytest.mark.anyio
async def test_file_index_crud(tmp_path: Path):
    db_file = str(tmp_path / "test_index.db")
    file_index = FileIndex(db_path=db_file)
    await file_index.initialize()

    # Upsert file
    await file_index.upsert_file(
        path="docs/architecture.md",
        title="architecture.md",
        content="Spectra uses an OrbStateMachine to manage state transitions.",
        last_modified=1234567.0
    )

    # Check last_modified
    mtime = await file_index.get_last_modified("docs/architecture.md")
    assert mtime == 1234567.0

    # Search for term
    results = await file_index.search("OrbStateMachine")
    assert len(results) == 1
    assert results[0]["path"] == "docs/architecture.md"
    assert "OrbStateMachine" in results[0]["content"]

    # Search non-matching term
    no_results = await file_index.search("nonexistent_keyword_xyz")
    assert len(no_results) == 0

    await file_index.close()

@pytest.mark.anyio
async def test_file_indexer_cooperative_batching(tmp_path: Path):
    db_file = str(tmp_path / "indexer.db")
    file_index = FileIndex(db_path=db_file)
    await file_index.initialize()

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # Create 15 dummy markdown files to test batching (batch size = 5)
    for i in range(15):
        (docs_dir / f"doc_{i}.md").write_text(f"Document {i} content about Spectra Phase {i}.", encoding="utf-8")

    indexer = FileIndexer(file_index=file_index, target_dir=str(docs_dir), batch_size=5)
    count = await indexer.run_index_pass()
    assert count == 15

    # Verify FTS5 query works
    res = await file_index.search("Phase 3")
    assert len(res) >= 1
    assert "Phase 3" in res[0]["content"]

    await file_index.close()

@pytest.mark.anyio
async def test_files_handler_augments_prompt(tmp_path: Path):
    db_file = str(tmp_path / "handler.db")
    file_index = FileIndex(db_path=db_file)
    await file_index.initialize()

    await file_index.upsert_file(
        path="docs/phase0.md",
        title="phase0.md",
        content="Phase 0 establishes FastAPI and Tauri integration.",
        last_modified=100.0
    )

    mock_talk = MockTalkHandler()
    handler = FilesHandler(file_index=file_index, talk_handler=mock_talk)

    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)
    
    # Direct text attachment
    text_attachment = Attachment(
        id="att1",
        mime_type="text/plain",
        storage=AttachmentStorage.INLINE,
        name="notes.txt",
        content="User extra note attached inline."
    )

    ctx = TaskContext(
        mode="files",
        text="Explain Phase 0",
        state_machine=state_machine,
        attachments=[text_attachment]
    )

    results = []
    async for event in handler.handle(ctx):
        results.append(event)

    # Verify augmented text passed to talk handler
    assert "Phase 0 establishes FastAPI and Tauri integration." in mock_talk.received_prompt
    assert "User extra note attached inline." in mock_talk.received_prompt

    await file_index.close()
