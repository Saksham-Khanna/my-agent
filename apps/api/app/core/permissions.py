import asyncio
import uuid
from typing import Dict, Optional, Tuple


class PermissionManager:
    """Manages asynchronous pending permission requests between backend handlers and frontend UI."""

    def __init__(self):
        self._pending_requests: Dict[str, asyncio.Future[bool]] = {}

    def create_request(self) -> Tuple[str, asyncio.Future[bool]]:
        """Generates a unique request_id and creates a Future for awaiting permission decision."""
        request_id = f"perm_{uuid.uuid4().hex[:8]}"
        loop = asyncio.get_running_loop()
        future: asyncio.Future[bool] = loop.create_future()
        self._pending_requests[request_id] = future
        return request_id, future

    def resolve_request(self, request_id: str, allowed: bool) -> bool:
        """Resolves a pending permission request with user decision (allowed=True/False)."""
        future = self._pending_requests.pop(request_id, None)
        if future and not future.done():
            future.set_result(allowed)
            return True
        return False

    def cancel_all(self) -> None:
        """Cancels all pending permission requests (e.g. on client disconnect)."""
        for future in self._pending_requests.values():
            if not future.done():
                future.set_result(False)
        self._pending_requests.clear()


permission_manager = PermissionManager()
