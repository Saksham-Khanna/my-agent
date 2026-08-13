import asyncio
import os
import platform
import sys
from pathlib import Path
from typing import Any, Optional

from app.tools.base import BaseTool, ToolDefinition, ToolResult
from app.tools.registry import default_registry


class ShellCommandTool(BaseTool):
    definition = ToolDefinition(
        name="shell_command",
        description="Execute a shell command locally on the system.",
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command string to execute in the terminal."
                },
                "cwd": {
                    "type": "string",
                    "description": "Optional working directory path."
                }
            },
            "required": ["command"]
        },
        requires_permission=True,
        risk_level="high"
    )

    async def execute(self, command: str, cwd: Optional[str] = None, **kwargs: Any) -> ToolResult:
        try:
            work_dir = cwd if cwd and os.path.isdir(cwd) else os.getcwd()
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=30.0)
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    success=False,
                    output="",
                    error="Command execution timed out after 30 seconds."
                )

            stdout_str = stdout_bytes.decode("utf-8", errors="replace")
            stderr_str = stderr_bytes.decode("utf-8", errors="replace")

            if process.returncode == 0:
                return ToolResult(
                    success=True,
                    output=stdout_str or "(No output)",
                    metadata={"returncode": 0}
                )
            else:
                return ToolResult(
                    success=False,
                    output=stdout_str,
                    error=stderr_str or f"Process exited with status code {process.returncode}",
                    metadata={"returncode": process.returncode}
                )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to execute shell command: {str(e)}"
            )


class CreateFileTool(BaseTool):
    definition = ToolDefinition(
        name="create_file",
        description="Create or overwrite a file on the local filesystem with specified content.",
        parameters={
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Target file path relative to workspace or absolute path."
                },
                "content": {
                    "type": "string",
                    "description": "The text content to write to the file."
                }
            },
            "required": ["filepath", "content"]
        },
        requires_permission=True,
        risk_level="medium"
    )

    async def execute(self, filepath: str, content: str, **kwargs: Any) -> ToolResult:
        try:
            target_path = Path(filepath).resolve()
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            target_path.write_text(content, encoding="utf-8")
            return ToolResult(
                success=True,
                output=f"Successfully created file: {target_path}",
                metadata={"filepath": str(target_path), "bytes_written": len(content.encode('utf-8'))}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to create file '{filepath}': {str(e)}"
            )


class SystemInfoTool(BaseTool):
    definition = ToolDefinition(
        name="system_info",
        description="Get basic system diagnostic information (OS, architecture, Python version).",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        },
        requires_permission=False,
        risk_level="low"
    )

    async def execute(self, **kwargs: Any) -> ToolResult:
        try:
            info = {
                "os": platform.system(),
                "os_release": platform.release(),
                "architecture": platform.machine(),
                "python_version": sys.version.split()[0],
                "cpu_count": os.cpu_count() or 1,
            }
            output = "System Info:\n" + "\n".join(f"  {k}: {v}" for k, v in info.items())
            return ToolResult(
                success=True,
                output=output,
                metadata=info
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to gather system info: {str(e)}"
            )


def register_default_tools(registry=default_registry) -> None:
    """Registers standard system tools into the provided registry."""
    registry.register(ShellCommandTool())
    registry.register(CreateFileTool())
    registry.register(SystemInfoTool())


# Automatically register standard tools
register_default_tools()
