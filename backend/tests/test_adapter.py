import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

from backend.services.llm.adapter import (
    LLMAdapter,
    ToolDefinition,
    _convert_messages_for_anthropic,
)


def test_system_extracted_and_conversation_starts_with_user():
    system, api = _convert_messages_for_anthropic(
        [
            {"role": "system", "content": "Be helpful."},
            {"role": "assistant", "content": "hi"},  # invalid opener for Anthropic
            {"role": "user", "content": "hello"},
        ]
    )
    assert system == "Be helpful."
    assert api[0]["role"] == "user"
    assert api[0]["content"][0]["text"] == "Continue."


def test_openai_tool_traffic_converted_to_anthropic_blocks():
    messages = [
        {"role": "system", "content": "You are a test agent."},
        {"role": "user", "content": "What's the weather in SF?"},
        {
            "role": "assistant",
            "content": "Let me check.",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": json.dumps({"city": "SF"}),
                    },
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": '{"temp": 72}'},
        {"role": "assistant", "content": "It is 72F in SF."},
    ]

    system, api = _convert_messages_for_anthropic(messages)

    assert system == "You are a test agent."
    roles = [m["role"] for m in api]
    assert roles == ["user", "assistant", "user", "assistant"]

    assistant = api[1]
    kinds = [b["type"] for b in assistant["content"]]
    assert kinds == ["text", "tool_use"]
    tool_use = assistant["content"][1]
    assert tool_use["id"] == "call_1"
    assert tool_use["name"] == "get_weather"
    assert tool_use["input"] == {"city": "SF"}

    tool_result_msg = api[2]
    assert tool_result_msg["content"][0] == {
        "type": "tool_result",
        "tool_use_id": "call_1",
        "content": '{"temp": 72}',
    }

    assert api[3]["content"][0]["text"] == "It is 72F in SF."


def test_multiple_tool_results_flush_as_one_user_message():
    messages = [
        {"role": "user", "content": "run two tools"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "a",
                    "type": "function",
                    "function": {"name": "t1", "arguments": "{}"},
                },
                {
                    "id": "b",
                    "type": "function",
                    "function": {"name": "t2", "arguments": "{}"},
                },
            ],
        },
        {"role": "tool", "tool_call_id": "a", "content": "r1"},
        {"role": "tool", "tool_call_id": "b", "content": "r2"},
    ]

    _, api = _convert_messages_for_anthropic(messages)
    roles = [m["role"] for m in api]
    assert roles == ["user", "assistant", "user"]
    results = api[2]["content"]
    assert [r["tool_use_id"] for r in results] == ["a", "b"]


def test_invalid_tool_arguments_become_empty_dict():
    messages = [
        {"role": "user", "content": "go"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "x",
                    "type": "function",
                    "function": {"name": "t", "arguments": "not json"},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "x", "content": "ok"},
    ]
    _, api = _convert_messages_for_anthropic(messages)
    tool_use = next(
        b for b in api[1]["content"] if b["type"] == "tool_use"
    )
    assert tool_use["input"] == {}


def test_empty_messages_yield_placeholder_user_message():
    _, api = _convert_messages_for_anthropic(
        [{"role": "system", "content": "only system"}]
    )
    assert api[0]["role"] == "user"


def test_complete_anthropic_sends_converted_format():
    captured: dict = {}

    async def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            content=[
                SimpleNamespace(type="text", text="Checking weather"),
                SimpleNamespace(
                    type="tool_use",
                    id="call_9",
                    name="get_weather",
                    input={"city": "SF"},
                ),
            ],
            usage=SimpleNamespace(input_tokens=30, output_tokens=20),
            stop_reason="tool_use",
        )

    adapter = LLMAdapter(provider="anthropic", model="claude-3-5-haiku-20241022")
    adapter._client = SimpleNamespace(messages=SimpleNamespace(create=AsyncMock(side_effect=fake_create)))

    tools = [
        ToolDefinition(
            name="get_weather",
            description="Get weather",
            parameters={"type": "object", "properties": {"city": {"type": "string"}}},
        )
    ]
    messages = [
        {"role": "system", "content": "Be helpful."},
        {"role": "user", "content": "weather in SF?"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": json.dumps({"city": "SF"}),
                    },
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": '{"temp": 72}'},
        {"role": "user", "content": "and tomorrow?"},
    ]

    import time as _time

    result = asyncio.run(adapter._complete_anthropic(messages, tools, _time.monotonic()))

    assert captured["system"] == "Be helpful."
    assert captured["tools"][0]["name"] == "get_weather"
    roles = [m["role"] for m in captured["messages"]]
    assert roles == ["user", "assistant", "user"]

    # tool_use/tool_result round-trip survived conversion
    kinds = [b["type"] for b in captured["messages"][1]["content"]]
    assert "tool_use" in kinds
    third = captured["messages"][2]["content"]
    assert third[0]["type"] == "tool_result"
    assert third[0]["tool_use_id"] == "call_1"
    assert any(b.get("text") == "and tomorrow?" for b in third)

    assert result.content == "Checking weather"
    assert result.tokens_used == 50
    assert result.finish_reason == "tool_use"
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "get_weather"
    assert result.tool_calls[0].arguments == {"city": "SF"}
    assert result.latency_ms >= 0
