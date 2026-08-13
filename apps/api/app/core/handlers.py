import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any, Tuple, Optional

from app.core.models import TaskContext, TaskResult
from app.core.state import OrbState
from app.llm.ollama_provider import OllamaProvider

class BaseHandler:
    async def handle(self, ctx: TaskContext) -> AsyncGenerator[Any, None]:
        """
        Processes the task context and yields events.
        Events can be:
        - OrbStateEvent: For state transitions
        - Tuple[str, dict]: For specific data events like ("llm.token", {"text": "..."})
        - TaskResult: Always yielded exactly once at the end to indicate completion/failure.
        """
        raise NotImplementedError
        yield  # Just to make it an async generator


class TalkHandler(BaseHandler):
    def __init__(self, scheduler=None):
        self.scheduler = scheduler

    @asynccontextmanager
    async def _provider(self):
        """Return a loaded provider via the scheduler, or a bare fallback."""
        if self.scheduler is not None:
            async with self.scheduler.acquire("llm") as provider:
                yield provider
            return
        yield OllamaProvider()

    async def handle(self, ctx: TaskContext) -> AsyncGenerator[Any, None]:
        try:
            event = ctx.state_machine.transition_to(OrbState.THINKING, reason="user_prompt_received")
            yield event
        except ValueError as e:
            yield TaskResult(status="failure", message=str(e))
            return

        async with self._provider() as provider:
            async for item in self._stream_response(ctx, provider):
                yield item

    async def _stream_response(self, ctx: TaskContext, provider) -> AsyncGenerator[Any, None]:
        try:
            first_token = True
            async for token in provider.generate_stream(ctx.text):
                if first_token:
                    try:
                        event = ctx.state_machine.transition_to(OrbState.RESPONDING, reason="llm_first_token")
                        yield event
                    except ValueError:
                        # State was hijacked by a concurrent task. Abort gracefully.
                        yield TaskResult(status="success", message="Aborted due to concurrent request")
                        return
                    first_token = False
                
                yield ("llm.token", {"text": token})
                
            if ctx.state_machine.current_state == OrbState.RESPONDING:
                try:
                    event = ctx.state_machine.transition_to(OrbState.IDLE, reason="llm_generation_finished")
                    yield event
                except ValueError:
                    pass
            
            yield TaskResult(status="success", message="Response completed")
        except Exception as e:
            try:
                event = ctx.state_machine.transition_to(OrbState.ERROR, reason=f"llm_error: {str(e)}")
                yield event
            except ValueError:
                pass
            
            yield ("llm.token", {"text": f"\n\n[Error: {str(e)}]"})
            
            await asyncio.sleep(2)
            if ctx.state_machine.current_state == OrbState.ERROR:
                try:
                    event = ctx.state_machine.transition_to(OrbState.IDLE, reason="error_timeout_recovery")
                    yield event
                except ValueError:
                    pass
                
            yield TaskResult(status="failure", message=str(e))


class StubHandler(BaseHandler):
    """A generic handler for modes that are not yet implemented."""
    def __init__(self, mode_name: str, required_phase: int):
        self.mode_name = mode_name
        self.required_phase = required_phase

    async def handle(self, ctx: TaskContext) -> AsyncGenerator[Any, None]:
        # We can simulate thinking, then realizing it's not implemented, then going to error
        try:
            event = ctx.state_machine.transition_to(OrbState.THINKING, reason="stub_handler_start")
            yield event
        except ValueError:
            pass

        await asyncio.sleep(0.5)

        try:
            event = ctx.state_machine.transition_to(OrbState.ERROR, reason=f"{self.mode_name}_not_implemented")
            yield event
        except ValueError:
            pass

        await asyncio.sleep(1.0)
        if ctx.state_machine.current_state == OrbState.ERROR:
            try:
                event = ctx.state_machine.transition_to(OrbState.IDLE, reason="stub_handler_recovery")
                yield event
            except ValueError:
                pass

        yield TaskResult(
            status="not_implemented", 
            message=f"{self.mode_name.capitalize()} mode requires Phase {self.required_phase}"
        )


class FilesHandler(BaseHandler):
    """Handler for Files mode requests (Phase 6 File Intelligence)."""
    def __init__(self, file_index = None, talk_handler: TalkHandler = None):
        self.file_index = file_index
        self.talk_handler = talk_handler or TalkHandler()

    async def handle(self, ctx: TaskContext) -> AsyncGenerator[Any, None]:
        from app.core.attachments import filter_attachments_by_mime_prefix
        from app.services.file_index import FileIndex
        from app.core.config import settings

        try:
            event = ctx.state_machine.transition_to(OrbState.THINKING, reason="files_search_start")
            yield event
        except ValueError as e:
            yield TaskResult(status="failure", message=str(e))
            return

        if self.file_index is None:
            self.file_index = FileIndex(db_path=settings.sqlite_db_path)
            await self.file_index.initialize()

        # 1. Gather text from direct attachments
        text_atts = filter_attachments_by_mime_prefix(ctx.attachments, "text/")
        attached_contexts = []
        for att in text_atts:
            if att.content:
                attached_contexts.append(f"--- Attachment: {att.name or 'file.txt'} ---\n{att.content}")

        # 2. Search local SQLite index
        search_results = await self.file_index.search(ctx.text, limit=5)
        indexed_contexts = []
        for res in search_results:
            indexed_contexts.append(f"--- File: {res['path']} ---\n{res['content']}")

        all_context = "\n\n".join(attached_contexts + indexed_contexts)

        user_text = ctx.text if ctx.text.strip() else "Summarize the provided file context."
        if all_context:
            augmented_text = f"[Local File Context]\n{all_context}\n\nUser Request: {user_text}"
        else:
            augmented_text = f"[No matching local files found]\nUser Request: {user_text}"

        augmented_ctx = TaskContext(
            mode="talk",
            text=augmented_text,
            state_machine=ctx.state_machine,
            task_id=ctx.task_id,
            timestamp=ctx.timestamp,
            attachments=ctx.attachments
        )

        async for item in self.talk_handler.handle(augmented_ctx):
            yield item


class VisionHandler(BaseHandler):
    """Handler for Vision mode requests."""
    def __init__(self, talk_handler: TalkHandler = None, scheduler=None):
        self.talk_handler = talk_handler or TalkHandler(scheduler=scheduler)
        self.scheduler = scheduler

    @asynccontextmanager
    async def _provider(self):
        """Return a loaded vision provider via the scheduler, or a bare fallback."""
        if self.scheduler is not None:
            async with self.scheduler.acquire("vision") as provider:
                yield provider
            return
        from app.llm.vision_provider import VisionProvider
        yield VisionProvider()

    async def handle(self, ctx: TaskContext) -> AsyncGenerator[Any, None]:
        from app.core.attachments import get_first_attachment_by_mime_prefix

        try:
            event = ctx.state_machine.transition_to(OrbState.VISION, reason="vision_analysis_start")
            yield event
        except ValueError as e:
            yield TaskResult(status="failure", message=str(e))
            return

        image_att = get_first_attachment_by_mime_prefix(ctx.attachments, "image/")
        if not image_att or not image_att.data_b64:
            try:
                event = ctx.state_machine.transition_to(OrbState.ERROR, reason="no_image_provided")
                yield event
            except ValueError:
                pass
            await asyncio.sleep(1.0)
            try:
                event = ctx.state_machine.transition_to(OrbState.IDLE, reason="error_recovery")
                yield event
            except ValueError:
                pass
            yield TaskResult(status="failure", message="No image provided for vision mode")
            return

        async with self._provider() as provider:
            try:
                description = await provider.analyze(image_att.data_b64)
            except Exception as e:
                try:
                    event = ctx.state_machine.transition_to(OrbState.ERROR, reason=f"vision_error: {str(e)}")
                    yield event
                except ValueError:
                    pass
                await asyncio.sleep(2.0)
                if ctx.state_machine.current_state == OrbState.ERROR:
                    try:
                        event = ctx.state_machine.transition_to(OrbState.IDLE, reason="error_timeout_recovery")
                        yield event
                    except ValueError:
                        pass
                yield TaskResult(status="failure", message=f"Vision analysis failed: {str(e)}")
                return

        yield ("vision.frame_analyzed", {
            "description": description,
            "attachment_id": image_att.id
        })

        user_text = ctx.text if ctx.text.strip() else "What is in this image?"
        augmented_text = f"[Image Description: {description}]\nUser Request: {user_text}"

        augmented_ctx = TaskContext(
            mode="talk",
            text=augmented_text,
            state_machine=ctx.state_machine,
            task_id=ctx.task_id,
            timestamp=ctx.timestamp,
            attachments=ctx.attachments
        )

        async for item in self.talk_handler.handle(augmented_ctx):
            yield item


class ActionsHandler(BaseHandler):
    """Handler for Actions mode requests (Phase 7 Tool Execution & Permission Gating)."""
    def __init__(self, tool_registry=None, talk_handler: TalkHandler = None):
        from app.tools.registry import default_registry
        self.tool_registry = tool_registry or default_registry
        self.talk_handler = talk_handler or TalkHandler()

    def _parse_tool_intent(self, text: str) -> Tuple[Optional[str], dict]:
        """Parses prompt text to detect explicit tool calls or keywords."""
        text_strip = text.strip()
        
        # 1. System info intent
        if any(kw in text_strip.lower() for kw in ["sysinfo", "system info", "system information", "os info", "specs"]):
            return "system_info", {}

        # 2. Create file intent (e.g. "create file hello.txt with content Hello World")
        if text_strip.lower().startswith("create file") or text_strip.lower().startswith("write file"):
            parts = text_strip.split(maxsplit=2)
            if len(parts) >= 3:
                filepath = parts[2].split()[0]
                content = parts[2][len(filepath):].strip()
                if content.lower().startswith("with ") or content.lower().startswith("containing "):
                    content = content.split(maxsplit=1)[1]
                return "create_file", {"filepath": filepath, "content": content or "Sample file content"}

        # 3. Shell command intent (e.g. "shell dir" or "run echo Hello")
        for prefix in ["shell ", "run command ", "execute command ", "run ", "exec "]:
            if text_strip.lower().startswith(prefix):
                cmd = text_strip[len(prefix):].strip()
                if cmd:
                    return "shell_command", {"command": cmd}

        return None, {}

    async def handle(self, ctx: TaskContext) -> AsyncGenerator[Any, None]:
        from app.core.permissions import permission_manager

        try:
            event = ctx.state_machine.transition_to(OrbState.THINKING, reason="actions_handler_start")
            yield event
        except ValueError as e:
            yield TaskResult(status="failure", message=str(e))
            return

        tool_name, tool_args = self._parse_tool_intent(ctx.text)
        
        if not tool_name:
            # Fallback: describe tools via TalkHandler
            tools_list = ", ".join(t.definition.name for t in self.tool_registry.list_tools())
            augmented_text = f"[Available System Tools: {tools_list}]\nUser Request: {ctx.text}"
            augmented_ctx = TaskContext(
                mode="talk",
                text=augmented_text,
                state_machine=ctx.state_machine,
                task_id=ctx.task_id,
                timestamp=ctx.timestamp,
                attachments=ctx.attachments
            )
            async for item in self.talk_handler.handle(augmented_ctx):
                yield item
            return

        tool = self.tool_registry.get(tool_name)
        if not tool:
            yield TaskResult(status="failure", message=f"Tool '{tool_name}' not found")
            return

        # Handle Permission Gating
        if tool.definition.requires_permission:
            request_id, future = permission_manager.create_request()
            
            desc = f"Arguments: {tool_args}"
            yield ("permission.requested", {
                "request_id": request_id,
                "title": f"Execute Tool: {tool.definition.name}",
                "description": desc,
                "risk_level": tool.definition.risk_level,
                "tool_name": tool.definition.name,
                "params": tool_args
            })

            try:
                allowed = await asyncio.wait_for(future, timeout=60.0)
            except asyncio.TimeoutError:
                allowed = False

            if not allowed:
                try:
                    event = ctx.state_machine.transition_to(OrbState.INTERRUPTED, reason="permission_denied")
                    yield event
                except ValueError:
                    pass
                yield ("llm.token", {"text": "\n[Action Cancelled: Permission denied by user]\n"})
                await asyncio.sleep(1.0)
                if ctx.state_machine.current_state == OrbState.INTERRUPTED:
                    try:
                        event = ctx.state_machine.transition_to(OrbState.IDLE, reason="interrupted_recovery")
                        yield event
                    except ValueError:
                        pass
                yield TaskResult(status="interrupted", message="Permission denied by user")
                return

        # Execute Tool
        try:
            event = ctx.state_machine.transition_to(OrbState.EXECUTING, reason=f"executing_{tool_name}")
            yield event
        except ValueError:
            pass

        tool_res = await tool.execute(**tool_args)
        
        output_text = tool_res.output if tool_res.success else f"Error: {tool_res.error}"
        yield ("llm.token", {"text": f"\n[Executed Tool '{tool_name}']\n{output_text}\n"})

        try:
            event = ctx.state_machine.transition_to(OrbState.IDLE, reason="tool_execution_finished")
            yield event
        except ValueError:
            pass

        status = "success" if tool_res.success else "failure"
        yield TaskResult(status=status, message=output_text)




class ScreenHandler(BaseHandler):
    def __init__(self, vision_handler: VisionHandler = None):
        self.vision_handler = vision_handler or VisionHandler()

    async def handle(self, ctx: TaskContext) -> AsyncGenerator[Any, None]:
        from app.core.attachments import get_first_attachment_by_mime_prefix

        image_att = get_first_attachment_by_mime_prefix(ctx.attachments, "image/")
        if not image_att or not image_att.data_b64:
            yield ("screen.capture_requested", {"message": "Screenshot required"})
            yield TaskResult(status="failure", message="No screenshot provided")
            return

        async for item in self.vision_handler.handle(ctx):
            yield item


class MemoryHandler(BaseHandler):
    def __init__(self, memory_service=None, talk_handler: TalkHandler = None):
        self.memory_service = memory_service
        self.talk_handler = talk_handler or TalkHandler()

    async def handle(self, ctx: TaskContext) -> AsyncGenerator[Any, None]:
        text = ctx.text.strip()

        if not text:
            yield TaskResult(status="failure", message="No text provided for memory operation")
            return

        text_lower = text.lower()

        if text_lower.startswith("remember that "):
            content = text[len("remember that "):].strip()
            if content:
                mem_id = await self.memory_service.remember(content, source_mode="memory")
                yield ("llm.token", {"text": f"\n[Memory stored: {mem_id[:8]}...]\n"})
                yield TaskResult(status="success", message=f"Memory stored: {mem_id[:8]}...")
                return

        if text_lower.startswith("store: "):
            content = text[len("store: "):].strip()
            if content:
                mem_id = await self.memory_service.remember(content, source_mode="memory")
                yield ("llm.token", {"text": f"\n[Memory stored: {mem_id[:8]}...]\n"})
                yield TaskResult(status="success", message=f"Memory stored: {mem_id[:8]}...")
                return

        if any(kw in text_lower for kw in ["clear all memories", "forget everything", "delete all memories"]):
            count = await self.memory_service.forget_all()
            yield ("llm.token", {"text": f"\n[Cleared {count} memory entr{( 'y' if count == 1 else 'ies' )}]\n"})
            yield TaskResult(status="success", message=f"Cleared {count} memory entries")
            return

        if any(kw in text_lower for kw in ["show memories", "list memories", "what do you remember", "display memories"]):
            entries = await self.memory_service.list_memories(limit=20)
            if not entries:
                yield ("llm.token", {"text": "\n[No memories stored yet]\n"})
            else:
                lines = ["\n[Stored Memories]"]
                for e in entries:
                    lines.append(f"- [{e.timestamp[:10]}] {e.content}")
                yield ("llm.token", {"text": "\n".join(lines) + "\n"})
            yield TaskResult(status="success", message="Memories listed")
            return

        entries = await self.memory_service.recall(text, limit=5)
        if entries:
            mem_text = "\n".join(f"- {e.content}" for e in entries)
            augmented_text = f"[Memories]\n{mem_text}\n\nUser Request: {text}"
        else:
            augmented_text = f"[No relevant memories found]\nUser Request: {text}"

        augmented_ctx = TaskContext(
            mode="talk",
            text=augmented_text,
            state_machine=ctx.state_machine,
            task_id=ctx.task_id,
            timestamp=ctx.timestamp,
            attachments=ctx.attachments
        )
        async for item in self.talk_handler.handle(augmented_ctx):
            yield item
