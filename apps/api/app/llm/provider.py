from abc import ABC, abstractmethod
from typing import AsyncGenerator

class LLMProvider(ABC):
    """
    Abstract base class for local LLM providers.
    Phase 1 scope: Only streaming text generation is required.
    Phase 9 scope: Lifecycle methods (load/unload/is_loaded) let the
    GPU-aware scheduler decide when this model is resident in memory.
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

    @abstractmethod
    async def load(self) -> None:
        """Load the model into memory. Must be idempotent."""
        pass

    @abstractmethod
    async def unload(self) -> None:
        """Release the model from memory. Must be idempotent."""
        pass

    @abstractmethod
    def is_loaded(self) -> bool:
        """Best-effort check of whether the model is currently resident."""
        pass
