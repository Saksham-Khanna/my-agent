import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.tools.registry import ToolRegistry
from app.tools.system_tools import ShellCommandTool, CreateFileTool, SystemInfoTool
from app.core.permissions import PermissionManager
from app.core.models import TaskContext
from app.core.state import OrbStateMachine
from app.core.handlers import ActionsHandler


@pytest.mark.anyio
async def test_tool_registry():
    registry = ToolRegistry()
    tool = SystemInfoTool()
    registry.register(tool)
    
    assert registry.get("system_info") is tool
    assert len(registry.list_tools()) == 1
    schemas = registry.get_schemas()
    assert schemas[0]["name"] == "system_info"
    assert schemas[0]["requires_permission"] is False


@pytest.mark.anyio
async def test_system_info_tool():
    tool = SystemInfoTool()
    res = await tool.execute()
    assert res.success is True
    assert "System Info" in res.output
    assert "os" in res.metadata


@pytest.mark.anyio
async def test_create_file_tool():
    tool = CreateFileTool()
    with TemporaryDirectory() as tmpdir:
        target_file = str(Path(tmpdir) / "test_out.txt")
        res = await tool.execute(filepath=target_file, content="Hello World!")
        assert res.success is True
        assert Path(target_file).exists()
        assert Path(target_file).read_text(encoding="utf-8") == "Hello World!"


@pytest.mark.anyio
async def test_shell_command_tool():
    tool = ShellCommandTool()
    res = await tool.execute(command='echo "Spectra Test"')
    assert res.success is True
    assert "Spectra Test" in res.output


@pytest.mark.anyio
async def test_permission_manager():
    pm = PermissionManager()
    req_id, fut = pm.create_request()
    assert req_id.startswith("perm_")
    assert not fut.done()
    
    resolved = pm.resolve_request(req_id, True)
    assert resolved is True
    assert fut.result() is True


@pytest.mark.anyio
async def test_actions_handler_sysinfo():
    handler = ActionsHandler()
    sm = OrbStateMachine()
    ctx = TaskContext(mode="actions", text="sysinfo", state_machine=sm)
    
    events = []
    async for event in handler.handle(ctx):
        events.append(event)

    # Last item must be TaskResult
    task_res = events[-1]
    assert task_res.status == "success"
    assert "System Info" in task_res.message
