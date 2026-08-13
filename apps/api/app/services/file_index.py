from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
import aiosqlite

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "what", "is", "the", "how", "does", "in", "to", "for", "of", "and", 
    "a", "an", "tell", "me", "about", "show", "explain", "describe", "can", "you"
}

def extract_keywords(query: str) -> List[str]:
    words = [w.strip() for w in query.split() if w.strip().isalnum()]
    keywords = [w for w in words if w.lower() not in STOP_WORDS]
    return keywords if keywords else words


class FileIndex:
    """
    Service isolating storage and FTS5 search operations for local file intelligence.
    """
    def __init__(self, db_path: str = "spectra_files.db"):
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            self._db = await aiosqlite.connect(self.db_path)
            self._db.row_factory = aiosqlite.Row
        return self._db

    async def initialize(self) -> None:
        """Initializes FTS5 virtual table schema."""
        db = await self._get_db()
        await db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS files_index USING fts5(
                path UNINDEXED,
                title,
                content,
                last_modified UNINDEXED
            );
        """)
        await db.commit()
        logger.info(f"FileIndex initialized at {self.db_path}")

    async def get_last_modified(self, path: str) -> Optional[float]:
        """Returns recorded last_modified timestamp for a given file path."""
        db = await self._get_db()
        async with db.execute("SELECT last_modified FROM files_index WHERE path = ?", (path,)) as cursor:
            row = await cursor.fetchone()
            if row and row["last_modified"] is not None:
                try:
                    return float(row["last_modified"])
                except ValueError:
                    return None
        return None

    async def upsert_file(self, path: str, title: str, content: str, last_modified: float) -> None:
        """Deletes existing entries for path and inserts updated title/content."""
        db = await self._get_db()
        await db.execute("DELETE FROM files_index WHERE path = ?", (path,))
        await db.execute(
            "INSERT INTO files_index(path, title, content, last_modified) VALUES (?, ?, ?, ?)",
            (path, title, content, str(last_modified))
        )
        await db.commit()

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches index using FTS5 MATCH with fallback to LIKE search."""
        if not query.strip():
            return []

        db = await self._get_db()
        results: List[Dict[str, Any]] = []

        keywords = extract_keywords(query)
        if not keywords:
            return []

        # 1. Try FTS5 OR search first for keyword matching
        fts_query = " OR ".join(f'"{kw}"' for kw in keywords)

        try:
            async with db.execute(
                "SELECT path, title, content FROM files_index WHERE files_index MATCH ? ORDER BY rank LIMIT ?",
                (fts_query, limit)
            ) as cursor:
                async for row in cursor:
                    results.append({
                        "path": row["path"],
                        "title": row["title"],
                        "content": row["content"]
                    })
        except Exception as e:
            logger.warning(f"FTS5 search query '{fts_query}' failed: {e}.")

        # 2. Fallback to LIKE search if FTS5 returned no results
        if not results:
            seen_paths = set()
            for kw in keywords:
                like_pattern = f"%{kw}%"
                async with db.execute(
                    "SELECT path, title, content FROM files_index WHERE content LIKE ? OR title LIKE ? LIMIT ?",
                    (like_pattern, like_pattern, limit)
                ) as cursor:
                    async for row in cursor:
                        p = row["path"]
                        if p not in seen_paths:
                            seen_paths.add(p)
                            results.append({
                                "path": p,
                                "title": row["title"],
                                "content": row["content"]
                            })
                        if len(results) >= limit:
                            break

        return results

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None
