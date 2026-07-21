from typing import AsyncGenerator, Any

from app.core.models import TaskContext, TaskResult
from app.core.handlers import BaseHandler, TalkHandler, StubHandler
from app.core.state import OrbStateEvent

class TaskRouter:
    def __init__(self):
        self.handlers = {
            "talk": TalkHandler(),
            "vision": StubHandler(mode_name="vision", required_phase=5),
            "screen": StubHandler(mode_name="screen", required_phase=6),  # or whatever phase screen is
            "files": StubHandler(mode_name="files", required_phase=6),
            "memory": StubHandler(mode_name="memory", required_phase=8),
            "actions": StubHandler(mode_name="actions", required_phase=7),
        }

    async def dispatch(self, ctx: TaskContext) -> AsyncGenerator[Any, None]:
        handler = self.handlers.get(ctx.mode)
        
        # 1. Emit task.started
        yield ("task.started", {
            "task_id": ctx.task_id,
            "mode": ctx.mode,
            "label": f"Processing request in {ctx.mode} mode"
        })

        if not handler:
            yield ("task.failed", {
                "task_id": ctx.task_id,
                "error": f"Unknown mode: {ctx.mode}"
            })
            return

        # 2. Iterate over handler events
        try:
            async for event in handler.handle(ctx):
                if isinstance(event, OrbStateEvent):
                    # Passthrough state events
                    yield event
                elif isinstance(event, TaskResult):
                    # 3. Finalize task
                    if event.status == "success":
                        yield ("task.completed", {
                            "task_id": ctx.task_id,
                            "message": event.message
                        })
                    else:
                        yield ("task.failed", {
                            "task_id": ctx.task_id,
                            "error": event.message,
                            "status": event.status
                        })
                elif isinstance(event, tuple):
                    # Passthrough specific events (e.g. llm.token)
                    yield event
                    
                    # Optionally emit task.progress when receiving tokens
                    if event[0] == "llm.token":
                        yield ("task.progress", {
                            "task_id": ctx.task_id,
                            "status": "generating"
                        })
        except Exception as e:
            yield ("task.failed", {
                "task_id": ctx.task_id,
                "error": f"Unexpected error during task execution: {str(e)}"
            })
