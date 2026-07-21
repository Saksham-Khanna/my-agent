import asyncio
from typing import AsyncGenerator, Any, Tuple

from app.core.models import TaskContext, TaskResult
from app.core.state import OrbState, OrbStateEvent
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
    async def handle(self, ctx: TaskContext) -> AsyncGenerator[Any, None]:
        try:
            event = ctx.state_machine.transition_to(OrbState.THINKING, reason="user_prompt_received")
            yield event
        except ValueError as e:
            yield TaskResult(status="failure", message=str(e))
            return
            
        provider = OllamaProvider()
        try:
            first_token = True
            async for token in provider.generate_stream(ctx.text):
                if first_token:
                    event = ctx.state_machine.transition_to(OrbState.RESPONDING, reason="llm_first_token")
                    yield event
                    first_token = False
                
                yield ("llm.token", {"text": token})
                
            event = ctx.state_machine.transition_to(OrbState.IDLE, reason="llm_generation_finished")
            yield event
            
            yield TaskResult(status="success", message="Response completed")
        except Exception as e:
            try:
                event = ctx.state_machine.transition_to(OrbState.ERROR, reason=f"llm_error: {str(e)}")
                yield event
            except ValueError:
                pass
            
            yield ("llm.token", {"text": f"\n\n[Error: {str(e)}]"})
            
            await asyncio.sleep(2)
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

        try:
            event = ctx.state_machine.transition_to(OrbState.IDLE, reason="stub_handler_recovery")
            yield event
        except ValueError:
            pass

        yield TaskResult(
            status="not_implemented", 
            message=f"{self.mode_name.capitalize()} mode requires Phase {self.required_phase}"
        )
