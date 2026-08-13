from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class RetrievalDecision:
    should_query: bool = False
    query_text: str = ""
    max_results: int = 5


MEMORY_KEYWORDS = {"remember", "last time", "previously", "what did i", "recall", "forget", "memory"}


class RetrievalPolicy:
    async def decide(self, mode: str, text: str, attachments: list) -> RetrievalDecision:
        raise NotImplementedError


class DefaultRetrievalPolicy(RetrievalPolicy):
    async def decide(self, mode: str, text: str, attachments: list) -> RetrievalDecision:
        text_stripped = text.strip()
        text_lower = text_stripped.lower()

        if mode in ("actions", "screen"):
            return RetrievalDecision(should_query=False)

        word_count = len(text_stripped.split()) if text_stripped else 0
        if word_count < 3:
            return RetrievalDecision(should_query=False)

        if "ignore memory" in text_lower:
            return RetrievalDecision(should_query=False)

        if mode in ("talk", "memory"):
            return RetrievalDecision(should_query=True, query_text=text_stripped, max_results=5)

        if mode in ("vision", "files"):
            if any(kw in text_lower for kw in MEMORY_KEYWORDS):
                return RetrievalDecision(should_query=True, query_text=text_stripped, max_results=5)

        return RetrievalDecision(should_query=False)
