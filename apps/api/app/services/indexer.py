from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional
from app.services.file_index import FileIndex

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".json", ".py", ".ts", ".tsx"}

class FileIndexer:
    """
    Crawls target directory for text/markdown files using cooperative batch processing.
    """
    def __init__(self, file_index: FileIndex, target_dir: str = "docs", batch_size: int = 10):
        self.file_index = file_index
        self.target_dir = Path(target_dir)
        self.batch_size = batch_size

    async def run_index_pass(self) -> int:
        """
        Scans target_dir and indexes new/updated files.
        Returns total number of files indexed.
        """
        if not self.target_dir.exists():
            logger.warning(f"Target index directory does not exist: {self.target_dir}")
            return 0

        indexed_count = 0
        processed_in_batch = 0

        # Gather files
        files_to_scan = [
            p for p in self.target_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        for file_path in files_to_scan:
            try:
                stat = file_path.stat()
                mtime = stat.st_mtime
                rel_path = str(file_path.as_posix())

                # Check if file has been updated
                recorded_mtime = await self.file_index.get_last_modified(rel_path)
                if recorded_mtime is not None and abs(recorded_mtime - mtime) < 0.001:
                    continue

                # Read and index content
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                title = file_path.name

                await self.file_index.upsert_file(
                    path=rel_path,
                    title=title,
                    content=content,
                    last_modified=mtime
                )
                indexed_count += 1
                processed_in_batch += 1

                # Cooperative batching: yield to asyncio event loop every batch_size files
                if processed_in_batch >= self.batch_size:
                    await asyncio.sleep(0)
                    processed_in_batch = 0

            except Exception as e:
                logger.error(f"Error indexing file {file_path}: {e}")

        logger.info(f"File index pass completed. Indexed/updated {indexed_count} files.")
        return indexed_count
