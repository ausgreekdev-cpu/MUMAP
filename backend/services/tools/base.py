from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import time
from pydantic import BaseModel


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict
    required: list[str] = []


@dataclass
class ToolResult:
    success: bool
    output: Any
    error: str | None = None
    duration_ms: int = 0
    metadata: dict = field(default_factory=dict)


class Tool(ABC):
    name: str
    description: str
    parameters: dict

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        pass

    def to_llm_schema(self) -> ToolDefinition:
        props = self.parameters.get("properties", {})
        required = self.parameters.get("required", [])
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
            required=required,
        )

    def validate_params(self, params: dict) -> bool:
        required = self.parameters.get("required", [])
        properties = self.parameters.get("properties", {})
        for key in required:
            if key not in params:
                return False
        for key, value in params.items():
            if key in properties and "type" in properties[key]:
                expected = properties[key]["type"]
                if expected == "string" and not isinstance(value, str):
                    return False
                elif expected == "integer" and not isinstance(value, int):
                    return False
                elif expected == "number" and not isinstance(value, (int, float)):
                    return False
                elif expected == "boolean" and not isinstance(value, bool):
                    return False
                elif expected == "object" and not isinstance(value, dict):
                    return False
                elif expected == "array" and not isinstance(value, list):
                    return False
        return True

    def _timed_execute(self, func, **kwargs):
        start = time.monotonic()
        try:
            result = func(**kwargs)
            duration = int((time.monotonic() - start) * 1000)
            return result, duration
        except Exception as e:
            duration = int((time.monotonic() - start) * 1000)
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                duration_ms=duration,
            ), duration
