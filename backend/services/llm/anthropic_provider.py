from __future__ import annotations

import time
import logging
from typing import AsyncGenerator, Optional

try:
    from anthropic import AsyncAnthropic, APIError, RateLimitError, APITimeoutError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base import LLMProvider, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)

SUPPORTED_MODELS = [
    "claude-sonnet-4-20250514",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
]

MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0


class AnthropicProvider(LLMProvider):

    def __init__(self, api_key: str):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package is required: pip install anthropic")
        self.client = AsyncAnthropic(api_key=api_key)

    def list_models(self) -> list[str]:
        return list(SUPPORTED_MODELS)

    def _split_messages(self, messages: list[LLMMessage]) -> tuple[Optional[str], list[dict]]:
        system_prompt = None
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})
        if not chat_messages:
            chat_messages.append({"role": "user", "content": "Hello"})
        return system_prompt, chat_messages

    async def complete(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        system_prompt, chat_messages = self._split_messages(messages)

        last_error: Optional[Exception] = None
        for attempt in range(1, MAX_RETRIES + 1):
            start = time.monotonic()
            try:
                kwargs: dict = {
                    "model": model,
                    "messages": chat_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if system_prompt:
                    kwargs["system"] = system_prompt

                response = await self.client.messages.create(**kwargs)
                latency = (time.monotonic() - start) * 1000

                content_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        content_text += block.text

                tokens = (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0
                finish = response.stop_reason or "end_turn"
                self._log_call(model, latency, tokens)

                return LLMResponse(
                    content=content_text,
                    model=response.model,
                    tokens_used=tokens,
                    finish_reason=finish,
                    latency_ms=latency,
                )
            except RateLimitError as exc:
                last_error = exc
                delay = RETRY_DELAY_BASE * (2 ** (attempt - 1))
                logger.warning("anthropic rate_limit attempt=%d delay=%.1f", attempt, delay)
                import asyncio
                await asyncio.sleep(delay)
            except APITimeoutError as exc:
                last_error = exc
                delay = RETRY_DELAY_BASE * (2 ** (attempt - 1))
                logger.warning("anthropic timeout attempt=%d delay=%.1f", attempt, delay)
                import asyncio
                await asyncio.sleep(delay)
            except APIError as exc:
                latency = (time.monotonic() - start) * 1000
                self._log_call(model, latency, 0, success=False)
                raise RuntimeError(f"Anthropic API error: {exc}") from exc
            except Exception as exc:
                latency = (time.monotonic() - start) * 1000
                self._log_call(model, latency, 0, success=False)
                raise RuntimeError(f"Anthropic request failed: {exc}") from exc

        latency = (time.monotonic() - start) * 1000
        self._log_call(model, latency, 0, success=False)
        raise RuntimeError(f"Anthropic max retries exceeded: {last_error}")

    async def stream(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        system_prompt, chat_messages = self._split_messages(messages)

        start = time.monotonic()
        try:
            kwargs: dict = {
                "model": model,
                "messages": chat_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            async with self.client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield text

            latency = (time.monotonic() - start) * 1000
            self._log_call(model, latency, 0)
        except Exception as exc:
            latency = (time.monotonic() - start) * 1000
            self._log_call(model, latency, 0, success=False)
            raise RuntimeError(f"Anthropic stream failed: {exc}") from exc
