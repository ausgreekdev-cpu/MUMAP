from typing import Any

from .base import Tool, ToolDefinition, ToolResult
from .web_search import web_search_tool
from .code_executor import code_executor_tool
from .file_reader import file_reader_tool
from .http_request import http_request_tool
from .calculator import calculator_tool
from .json_parser import json_parser_tool


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def list_schemas(self) -> list[ToolDefinition]:
        return [tool.to_llm_schema() for tool in self._tools.values()]

    async def execute(self, name: str, **kwargs) -> ToolResult:
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool not found: {name}",
                metadata={"available_tools": list(self._tools.keys())},
            )
        if not tool.validate_params(kwargs):
            return ToolResult(
                success=False,
                output=None,
                error=f"Invalid parameters for tool: {name}",
                metadata={"expected": tool.parameters},
            )
        return await tool.execute(**kwargs)

    def unregister(self, name: str) -> bool:
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def has(self, name: str) -> bool:
        return name in self._tools


registry = ToolRegistry()

registry.register(web_search_tool)
registry.register(code_executor_tool)
registry.register(file_reader_tool)
registry.register(http_request_tool)
registry.register(calculator_tool)
registry.register(json_parser_tool)
