from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
import uuid

from app.core.state import OrbStateMachine

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _generate_task_id() -> str:
    return f"task_{uuid.uuid4().hex[:8]}"

@dataclass
class TaskContext:
    mode: str
    text: str
    state_machine: OrbStateMachine
    task_id: str = field(default_factory=_generate_task_id)
    timestamp: str = field(default_factory=_now_iso)

@dataclass
class TaskResult:
    status: str  # e.g., "success", "failure", "not_implemented"
    message: Optional[str] = None
