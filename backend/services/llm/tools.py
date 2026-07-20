from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class ToolResult:
    tool_call_id: str
    content: str
    is_error: bool = False


def tool_to_openai(tool: ToolDefinition) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


def tool_to_anthropic(tool: ToolDefinition) -> dict:
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.parameters,
    }


def tools_to_openai(tools: list[ToolDefinition]) -> list[dict]:
    return [tool_to_openai(t) for t in tools]


def tools_to_anthropic(tools: list[ToolDefinition]) -> list[dict]:
    return [tool_to_anthropic(t) for t in tools]


def parse_tool_calls_openai(response_data: dict) -> list[ToolCall]:
    calls = []
    choices = response_data.get("choices", [])
    if not choices:
        return calls

    message = choices[0].get("message", {})
    raw_calls = message.get("tool_calls") or []

    for tc in raw_calls:
        func = tc.get("function", {})
        args_raw = func.get("arguments", "{}")
        try:
            args = json.loads(args_raw)
        except (json.JSONDecodeError, TypeError):
            args = {"raw": args_raw}

        calls.append(ToolCall(
            id=tc.get("id", ""),
            name=func.get("name", ""),
            arguments=args,
        ))

    return calls


def parse_tool_calls_anthropic(response_data: dict) -> list[ToolCall]:
    calls = []
    content_blocks = response_data.get("content", [])

    for block in content_blocks:
        if block.get("type") == "tool_use":
            calls.append(ToolCall(
                id=block.get("id", ""),
                name=block.get("name", ""),
                arguments=block.get("input", {}),
            ))

    return calls


def tool_results_to_openai(results: list[ToolResult]) -> list[dict]:
    return [
        {
            "role": "tool",
            "tool_call_id": r.tool_call_id,
            "content": r.content,
        }
        for r in results
    ]


def tool_results_to_anthropic(results: list[ToolResult]) -> list[dict]:
    return [
        {
            "type": "tool_result",
            "tool_use_id": r.tool_call_id,
            "content": r.content,
            "is_error": r.is_error,
        }
        for r in results
    ]
