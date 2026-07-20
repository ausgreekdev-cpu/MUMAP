import json
import re
import time
from typing import Any

from .base import Tool, ToolResult


class JsonParserTool(Tool):
    name = "json_parser"
    description = "Extract and parse JSON data from text. Optionally validate against a schema."
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text containing JSON data to extract",
            },
            "schema": {
                "type": "object",
                "description": "Optional JSON schema to validate against",
            },
        },
        "required": ["text"],
    }

    JSON_PATTERNS = [
        re.compile(r"```json\s*\n?(.*?)\n?\s*```", re.DOTALL),
        re.compile(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", re.DOTALL),
        re.compile(r"\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]", re.DOTALL),
    ]

    async def execute(self, text: str, schema: dict | None = None, **kwargs) -> ToolResult:
        start = time.monotonic()
        try:
            if not text.strip():
                return ToolResult(
                    success=False,
                    output=None,
                    error="Text cannot be empty",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            parsed_objects = self._extract_json(text)

            if not parsed_objects:
                return ToolResult(
                    success=False,
                    output=None,
                    error="No valid JSON found in text",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            validated = []
            if schema:
                for obj in parsed_objects:
                    if self._validate_schema(obj, schema):
                        validated.append(obj)
                results = validated if validated else parsed_objects
                is_valid = bool(validated)
            else:
                results = parsed_objects
                is_valid = True

            duration = int((time.monotonic() - start) * 1000)
            output = results if len(results) > 1 else results[0]

            return ToolResult(
                success=True,
                output=output,
                duration_ms=duration,
                metadata={
                    "found_count": len(parsed_objects),
                    "valid_count": len(validated) if schema else len(parsed_objects),
                    "schema_validation": schema is not None,
                    "schema_valid": is_valid if schema else None,
                },
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

    def _extract_json(self, text: str) -> list[Any]:
        results = []
        seen = set()

        try:
            obj = json.loads(text)
            key = json.dumps(obj, sort_keys=True)
            if key not in seen:
                seen.add(key)
                results.append(obj)
        except (json.JSONDecodeError, ValueError):
            pass

        for pattern in self.JSON_PATTERNS:
            for match in pattern.finditer(text):
                candidate = match.group(1) if pattern == self.JSON_PATTERNS[0] else match.group(0)
                try:
                    obj = json.loads(candidate)
                    key = json.dumps(obj, sort_keys=True)
                    if key not in seen:
                        seen.add(key)
                        results.append(obj)
                except (json.JSONDecodeError, ValueError):
                    continue

        return results

    def _validate_schema(self, data: Any, schema: dict) -> bool:
        schema_type = schema.get("type")

        if schema_type == "object":
            if not isinstance(data, dict):
                return False
            required = schema.get("required", [])
            for field in required:
                if field not in data:
                    return False
            properties = schema.get("properties", {})
            for key, value in data.items():
                if key in properties:
                    if not self._validate_schema(value, properties[key]):
                        return False
            return True
        elif schema_type == "array":
            if not isinstance(data, list):
                return False
            items_schema = schema.get("items")
            if items_schema:
                return all(self._validate_schema(item, items_schema) for item in data)
            return True
        elif schema_type == "string":
            return isinstance(data, str)
        elif schema_type == "number":
            return isinstance(data, (int, float))
        elif schema_type == "integer":
            return isinstance(data, int)
        elif schema_type == "boolean":
            return isinstance(data, bool)
        elif schema_type == "null":
            return data is None
        elif "enum" in schema:
            return data in schema["enum"]
        return True


json_parser_tool = JsonParserTool()
