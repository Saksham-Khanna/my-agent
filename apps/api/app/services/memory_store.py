from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import uuid
import aiosqlite

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    id: str = field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:12]}")
    content: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    session_id: str = ""
    source_mode: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryStore:
    def __init__(self, db_path: str = "spectra_memory.db"):
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            self._db = await aiosqlite.connect(self.db_path)
            self._db.row_factory = aiosqlite.Row
        return self._db

    async def initialize(self) -> None:
        db = await self._get_db()
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memory_entries (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                session_id TEXT NOT NULL,
                source_mode TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}'
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory_entries(timestamp DESC)
        """)
        await db.commit()
        logger.info(f"MemoryStore initialized at {self.db_path}")

    async def store(self, entry: MemoryEntry) -> str:
        db = await self._get_db()
        await db.execute(
            "INSERT INTO memory_entries(id, content, timestamp, session_id, source_mode, metadata) VALUES (?, ?, ?, ?, ?, ?)",
            (entry.id, entry.content, entry.timestamp, entry.session_id, entry.source_mode, json.dumps(entry.metadata))
        )
        await db.commit()
        return entry.id

    async def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        if not query.strip():
            return []
        db = await self._get_db()
        like_pattern = f"%{query}%"
        rows = []
        async with db.execute(
            "SELECT id, content, timestamp, session_id, source_mode, metadata FROM memory_entries WHERE content LIKE ? ORDER BY timestamp DESC, rowid DESC LIMIT ?",
            (like_pattern, limit)
        ) as cursor:
            async for row in cursor:
                rows.append(self._row_to_entry(row))
        return rows

    async def get_recent(self, limit: int = 20) -> List[MemoryEntry]:
        db = await self._get_db()
        rows = []
        async with db.execute(
            "SELECT id, content, timestamp, session_id, source_mode, metadata FROM memory_entries ORDER BY timestamp DESC, rowid DESC LIMIT ?",
            (limit,)
        ) as cursor:
            async for row in cursor:
                rows.append(self._row_to_entry(row))
        return rows

    async def get_by_id(self, id: str) -> Optional[MemoryEntry]:
        db = await self._get_db()
        async with db.execute(
            "SELECT id, content, timestamp, session_id, source_mode, metadata FROM memory_entries WHERE id = ?",
            (id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_entry(row)
        return None

    async def clear_all(self) -> int:
        db = await self._get_db()
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM memory_entries")
        row = await cursor.fetchone()
        count = row["cnt"] if row else 0
        await db.execute("DELETE FROM memory_entries")
        await db.commit()
        return count

    async def get_stats(self) -> Dict[str, Any]:
        db = await self._get_db()
        async with db.execute(
            "SELECT COUNT(*) as total, MIN(timestamp) as oldest, MAX(timestamp) as newest FROM memory_entries"
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "total": row["total"],
                    "oldest": row["oldest"],
                    "newest": row["newest"]
                }
        return {"total": 0, "oldest": None, "newest": None}

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    def _row_to_entry(self, row: aiosqlite.Row) -> MemoryEntry:
        meta = {}
        raw = row["metadata"]
        if raw:
            try:
                meta = json.loads(raw) if isinstance(raw, str) else raw
            except (json.JSONDecodeError, TypeError):
                meta = {}
        return MemoryEntry(
            id=row["id"],
            content=row["content"],
            timestamp=row["timestamp"],
            session_id=row["session_id"],
            source_mode=row["source_mode"],
            metadata=meta
        )
