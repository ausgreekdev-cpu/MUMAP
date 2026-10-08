from __future__ import annotations

import json
import time
import logging
import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional

from ...config import settings

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class LLMToolResponse:
    content: Optional[str]
    tool_calls: list[ToolCall]
    model: str
    tokens_used: int = 0
    finish_reason: str = "stop"
    latency_ms: float = 0.0


def _convert_messages_for_anthropic(
    messages: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    """Convert OpenAI-style chat messages to Anthropic's message format.

    The execution engine emits OpenAI-shaped tool traffic (assistant messages
    with ``tool_calls`` followed by ``role: "tool"`` results). Anthropic instead
    requires ``tool_use`` blocks on the assistant message and ``tool_result``
    blocks inside the immediately following user message, with strictly
    alternating roles starting with ``user``.

    Returns ``(system_text, api_messages)``.
    """
    system_parts: list[str] = []
    converted: list[dict[str, Any]] = []
    pending_tool_results: list[dict[str, Any]] = []

    def as_blocks(content: Any) -> list[dict[str, Any]]:
        if content is None:
            return []
        if isinstance(content, str):
            return [{"type": "text", "text": content}] if content else []
        if isinstance(content, list):
            return list(content)
        return [{"type": "text", "text": str(content)}]

    def push(role: str, blocks: list[dict[str, Any]]) -> None:
        if not blocks:
            return
        if converted and converted[-1]["role"] == role:
            converted[-1]["content"].extend(blocks)
        else:
            converted.append({"role": role, "content": blocks})

    for msg in messages:
        role = msg.get("role")

        if role == "system":
            text = msg.get("content") or ""
            if text:
                system_parts.append(text)
            continue

        if role == "tool":
            pending_tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": msg.get("tool_call_id") or msg.get("id") or "",
                    "content": msg.get("content") or "(no result)",
                }
            )
            continue

        # tool_result blocks must immediately follow the assistant tool_use
        # message, so flush them as a user message before other content.
        if pending_tool_results:
            push("user", pending_tool_results)
            pending_tool_results = []

        if role == "assistant":
            blocks = as_blocks(msg.get("content"))
            for tc in msg.get("tool_calls") or []:
                fn = tc.get("function") or {}
                raw_args = fn.get("arguments", "{}")
                if isinstance(raw_args, str):
                    try:
                        args = json.loads(raw_args)
                    except (json.JSONDecodeError, TypeError):
                        args = {}
                elif isinstance(raw_args, dict):
                    args = raw_args
                else:
                    args = {}
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": tc.get("id") or "",
                        "name": fn.get("name") or "",
                        "input": args,
                    }
                )
            push("assistant", blocks)
        else:
            push("user", as_blocks(msg.get("content")))

    if pending_tool_results:
        push("user", pending_tool_results)

    # Anthropic requires the conversation to start with a user message.
    if not converted:
        converted.append({"role": "user", "content": [{"type": "text", "text": "."}]})
    elif converted[0]["role"] != "user":
        converted.insert(
            0, {"role": "user", "content": [{"type": "text", "text": "Continue."}]}
        )

    return "\n".join(system_parts), converted


class LLMAdapter:
    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int | None = None,
    ):
        self.provider = provider or settings.LLM_DEFAULT_PROVIDER
        self.model = model or settings.LLM_DEFAULT_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout or settings.LLM_REQUEST_TIMEOUT
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        if self.provider == "openai":
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError(
                    "openai package not installed. Install with: pip install openai"
                )
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            self._client = AsyncOpenAI(api_key=api_key, timeout=self.timeout)

        elif self.provider == "anthropic":
            try:
                from anthropic import AsyncAnthropic
            except ImportError:
                raise ImportError(
                    "anthropic package not installed. Install with: pip install anthropic"
                )
            api_key = settings.ANTHROPIC_API_KEY
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            self._client = AsyncAnthropic(api_key=api_key, timeout=self.timeout)

        elif self.provider == "ollama":
            try:
                import httpx
            except ImportError:
                raise ImportError(
                    "httpx package not installed. Install with: pip install httpx"
                )
            self._client = httpx.AsyncClient(
                base_url=settings.OLLAMA_BASE_URL, timeout=self.timeout
            )

        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        return self._client

    def _to_openai_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    def _to_anthropic_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
            }
            for t in tools
        ]

    def _parse_openai_tool_calls(self, choice: Any) -> list[ToolCall]:
        tool_calls = []
        if not choice.message or not choice.message.tool_calls:
            return tool_calls
        for tc in choice.message.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except (json.JSONDecodeError, TypeError):
                args = {}
            tool_calls.append(
                ToolCall(id=tc.id, name=tc.function.name, arguments=args)
            )
        return tool_calls

    def _count_usage(self, usage: Any) -> int:
        if not usage:
            return 0
        total = 0
        if hasattr(usage, "total_tokens"):
            total = usage.total_tokens
        elif hasattr(usage, "input_tokens") and hasattr(usage, "output_tokens"):
            total = usage.input_tokens + usage.output_tokens
        return total or 0

    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMToolResponse:
        start = time.monotonic()

        try:
            if self.provider == "openai":
                return await self._complete_openai(messages, tools, start)
            elif self.provider == "anthropic":
                return await self._complete_anthropic(messages, tools, start)
            elif self.provider == "ollama":
                return await self._complete_ollama(messages, tools, start)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            logger.error(
                "llm_call_failed",
                extra={
                    "provider": self.provider,
                    "model": self.model,
                    "latency_ms": round(latency, 2),
                    "error": str(e),
                },
            )
            raise

    async def _complete_openai(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None,
        start: float,
    ) -> LLMToolResponse:
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            kwargs["tools"] = self._to_openai_tools(tools)
            kwargs["tool_choice"] = "auto"

        response = await client.chat.completions.create(**kwargs)
        latency = (time.monotonic() - start) * 1000
        choice = response.choices[0]
        content = choice.message.content if choice.message else None
        tool_calls = self._parse_openai_tool_calls(choice)
        tokens = self._count_usage(response.usage)

        logger.info(
            "llm_call_success",
            extra={
                "provider": "openai",
                "model": self.model,
                "latency_ms": round(latency, 2),
                "tokens": tokens,
                "tool_calls": len(tool_calls),
            },
        )

        return LLMToolResponse(
            content=content,
            tool_calls=tool_calls,
            model=self.model,
            tokens_used=tokens,
            finish_reason=choice.finish_reason or "stop",
            latency_ms=latency,
        )

    async def _complete_anthropic(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None,
        start: float,
    ) -> LLMToolResponse:
        client = self._get_client()

        system_text, api_messages = _convert_messages_for_anthropic(messages)

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if system_text.strip():
            kwargs["system"] = system_text.strip()
        if tools:
            kwargs["tools"] = self._to_anthropic_tools(tools)

        response = await client.messages.create(**kwargs)
        latency = (time.monotonic() - start) * 1000

        content_text = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content_text += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(id=block.id, name=block.name, arguments=block.input)
                )

        tokens = 0
        if response.usage:
            tokens = response.usage.input_tokens + response.usage.output_tokens

        logger.info(
            "llm_call_success",
            extra={
                "provider": "anthropic",
                "model": self.model,
                "latency_ms": round(latency, 2),
                "tokens": tokens,
                "tool_calls": len(tool_calls),
            },
        )

        return LLMToolResponse(
            content=content_text or None,
            tool_calls=tool_calls,
            model=self.model,
            tokens_used=tokens,
            finish_reason=response.stop_reason or "end_turn",
            latency_ms=latency,
        )

    async def _complete_ollama(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None,
        start: float,
    ) -> LLMToolResponse:
        client = self._get_client()

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }
        if tools:
            ollama_tools = []
            for t in tools:
                ollama_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.parameters,
                        },
                    }
                )
            payload["tools"] = ollama_tools

        response = await client.post("/api/chat", json=payload)
        latency = (time.monotonic() - start) * 1000
        response.raise_for_status()
        data = response.json()

        message = data.get("message", {})
        content = message.get("content")
        tool_calls = []
        for tc in message.get("tool_calls", []):
            func = tc.get("function", {})
            try:
                args = json.loads(func.get("arguments", "{}"))
            except (json.JSONDecodeError, TypeError):
                args = {}
            tool_calls.append(
                ToolCall(
                    id=f"ollama_{int(time.time()*1000)}",
                    name=func.get("name", ""),
                    arguments=args,
                )
            )

        tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)

        logger.info(
            "llm_call_success",
            extra={
                "provider": "ollama",
                "model": self.model,
                "latency_ms": round(latency, 2),
                "tokens": tokens,
                "tool_calls": len(tool_calls),
            },
        )

        return LLMToolResponse(
            content=content,
            tool_calls=tool_calls,
            model=self.model,
            tokens_used=tokens,
            finish_reason="stop",
            latency_ms=latency,
        )
