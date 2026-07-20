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

        system_text = ""
        api_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_text += msg["content"] + "\n"
            else:
                api_messages.append(msg)

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
