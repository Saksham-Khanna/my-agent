from __future__ import annotations

import logging
from typing import List, Optional, Callable, Awaitable

from app.services.memory_store import MemoryStore, MemoryEntry

logger = logging.getLogger(__name__)


class MemoryService:
    def __init__(self, store: MemoryStore, on_updated: Optional[Callable[[dict], Awaitable[None]]] = None):
        self.store = store
        self.on_updated = on_updated

    async def remember(self, content: str, source_mode: str = "memory", metadata: dict = None) -> str:
        entry = MemoryEntry(
            content=content,
            session_id="default",
            source_mode=source_mode,
            metadata=metadata or {}
        )
        entry_id = await self.store.store(entry)
        if self.on_updated:
            await self.on_updated({"action": "stored", "count": 1})
        logger.info(f"Memory stored: {entry_id[:16]}...")
        return entry_id

    async def recall(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        return await self.store.search(query, limit=limit)

    async def list_memories(self, limit: int = 20) -> List[MemoryEntry]:
        return await self.store.get_recent(limit=limit)

    async def forget_all(self) -> int:
        count = await self.store.clear_all()
        if self.on_updated:
            await self.on_updated({"action": "cleared", "count": count})
        logger.info(f"Memory cleared: {count} entries removed")
        return count

    async def get_memory_context(self, query: str, max_tokens: int = 2000) -> str:
        entries = await self.store.search(query, limit=5)
        if not entries:
            return ""
        lines = ["[Relevant Memories]"]
        for e in entries:
            content = e.content[:max_tokens // 5]
            lines.append(f"- {content}")
        return "\n".join(lines)
