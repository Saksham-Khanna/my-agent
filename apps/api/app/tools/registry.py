from typing import Dict, List, Optional, Any
from app.tools.base import BaseTool


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        name = tool.definition.name
        self._tools[name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Get registered tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Return tool definitions as a list of dictionary schemas."""
        schemas = []
        for tool in self._tools.values():
            d = tool.definition
            schemas.append({
                "name": d.name,
                "description": d.description,
                "parameters": d.parameters,
                "requires_permission": d.requires_permission,
                "risk_level": d.risk_level,
            })
        return schemas


# Global default registry instance
default_registry = ToolRegistry()
