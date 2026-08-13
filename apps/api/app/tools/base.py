from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Literal
from abc import ABC, abstractmethod


RiskLevel = Literal["low", "medium", "high"]


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for parameters
    requires_permission: bool = True
    risk_level: RiskLevel = "medium"


@dataclass
class ToolResult:
    success: bool
    output: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseTool(ABC):
    definition: ToolDefinition

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Executes the tool with given parameter kwargs."""
        pass
