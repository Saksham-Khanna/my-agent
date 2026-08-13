from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid

from app.core.state import OrbStateMachine

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _generate_task_id() -> str:
    return f"task_{uuid.uuid4().hex[:8]}"

class AttachmentStorage(str, Enum):
    INLINE = "inline"
    PATH = "path"
    URL = "url"

@dataclass(frozen=True)
class Attachment:
    id: str
    mime_type: str
    storage: AttachmentStorage = AttachmentStorage.INLINE
    name: Optional[str] = None
    data_b64: Optional[str] = None
    content: Optional[str] = None
    path: Optional[str] = None
    url: Optional[str] = None
    size_bytes: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.storage == AttachmentStorage.INLINE and not (self.data_b64 or self.content is not None):
            raise ValueError(f"Attachment '{self.id}' with storage INLINE requires 'data_b64' or 'content'")
        if self.storage == AttachmentStorage.PATH and not self.path:
            raise ValueError(f"Attachment '{self.id}' with storage PATH requires 'path'")
        if self.storage == AttachmentStorage.URL and not self.url:
            raise ValueError(f"Attachment '{self.id}' with storage URL requires 'url'")

@dataclass
class TaskContext:
    mode: str
    text: str
    state_machine: OrbStateMachine
    task_id: str = field(default_factory=_generate_task_id)
    timestamp: str = field(default_factory=_now_iso)
    attachments: List[Attachment] = field(default_factory=list)

@dataclass
class TaskResult:
    status: str  # e.g., "success", "failure", "not_implemented"
    message: Optional[str] = None
    attachments: List[Attachment] = field(default_factory=list)
