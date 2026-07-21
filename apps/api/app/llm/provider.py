from abc import ABC, abstractmethod
from typing import AsyncGenerator

class LLMProvider(ABC):
    """
    Abstract base class for local LLM providers.
    Phase 1 scope: Only streaming text generation is required.
    """

    @abstractmethod
    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Given a prompt, asynchronously yield chunks of text as they are generated.
        """
        pass
        # Note: the yield statement must be implemented in the subclasses.
        # This is an abstract async generator.
        if False:
            yield ""
