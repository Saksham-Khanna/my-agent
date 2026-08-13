from typing import AsyncGenerator, Any, Optional

from app.core.models import TaskContext, TaskResult
from app.core.handlers import TalkHandler, VisionHandler, FilesHandler, ActionsHandler, ScreenHandler, MemoryHandler
from app.core.state import OrbStateEvent
from app.core.memory_policy import RetrievalPolicy, DefaultRetrievalPolicy
from app.services.memory_service import MemoryService


class TaskRouter:
    def __init__(self, memory_service: Optional[MemoryService] = None, memory_policy: Optional[RetrievalPolicy] = None, scheduler=None):
        self.memory_service = memory_service
        self.memory_policy = memory_policy or DefaultRetrievalPolicy()
        talk_handler = TalkHandler(scheduler=scheduler)
        vision_handler = VisionHandler(scheduler=scheduler)
        self.handlers = {
            "talk": talk_handler,
            "vision": vision_handler,
            "files": FilesHandler(talk_handler=talk_handler),
            "actions": ActionsHandler(talk_handler=talk_handler),
            "screen": ScreenHandler(vision_handler=vision_handler),
            "memory": MemoryHandler(memory_service=self.memory_service, talk_handler=talk_handler),
        }

    async def dispatch(self, ctx: TaskContext) -> AsyncGenerator[Any, None]:
        # 0. Memory retrieval (pre-handler)
        decision = await self.memory_policy.decide(ctx.mode, ctx.text, ctx.attachments)
        memory_context = ""
        if decision.should_query and self.memory_service:
            memory_context = await self.memory_service.get_memory_context(
                query=decision.query_text,
                max_tokens=1500
            )
        if memory_context:
            ctx.text = f"{memory_context}\n\nUser Request: {ctx.text}"

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
                    yield event
                elif isinstance(event, TaskResult):
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
                    yield event
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
