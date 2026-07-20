from __future__ import annotations

import time
import logging
from typing import AsyncGenerator, Optional

try:
    from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import LLMProvider, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)

SUPPORTED_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
]

MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0


class OpenAIProvider(LLMProvider):

    def __init__(self, api_key: str, organization_id: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package is required: pip install openai")
        self.client = AsyncOpenAI(api_key=api_key, organization=organization_id)

    def list_models(self) -> list[str]:
        return list(SUPPORTED_MODELS)

    def _build_params(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> dict:
        return {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    async def complete(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        last_error: Optional[Exception] = None
        for attempt in range(1, MAX_RETRIES + 1):
            start = time.monotonic()
            try:
                params = self._build_params(messages, model, temperature, max_tokens)
                response = await self.client.chat.completions.create(**params)
                latency = (time.monotonic() - start) * 1000

                choice = response.choices[0]
                tokens = response.usage.total_tokens if response.usage else 0
                self._log_call(model, latency, tokens)

                return LLMResponse(
                    content=choice.message.content or "",
                    model=response.model,
                    tokens_used=tokens,
                    finish_reason=choice.finish_reason or "stop",
                    latency_ms=latency,
                )
            except RateLimitError as exc:
                last_error = exc
                delay = RETRY_DELAY_BASE * (2 ** (attempt - 1))
                logger.warning("openai rate_limit attempt=%d delay=%.1f", attempt, delay)
                import asyncio
                await asyncio.sleep(delay)
            except APITimeoutError as exc:
                last_error = exc
                delay = RETRY_DELAY_BASE * (2 ** (attempt - 1))
                logger.warning("openai timeout attempt=%d delay=%.1f", attempt, delay)
                import asyncio
                await asyncio.sleep(delay)
            except APIError as exc:
                latency = (time.monotonic() - start) * 1000
                self._log_call(model, latency, 0, success=False)
                raise RuntimeError(f"OpenAI API error: {exc}") from exc
            except Exception as exc:
                latency = (time.monotonic() - start) * 1000
                self._log_call(model, latency, 0, success=False)
                raise RuntimeError(f"OpenAI request failed: {exc}") from exc

        latency = (time.monotonic() - start) * 1000
        self._log_call(model, latency, 0, success=False)
        raise RuntimeError(f"OpenAI max retries exceeded: {last_error}")

    async def stream(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        params = self._build_params(messages, model, temperature, max_tokens)
        params["stream"] = True

        start = time.monotonic()
        try:
            response = await self.client.chat.completions.create(**params)
            async for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
            latency = (time.monotonic() - start) * 1000
            self._log_call(model, latency, 0)
        except Exception as exc:
            latency = (time.monotonic() - start) * 1000
            self._log_call(model, latency, 0, success=False)
            raise RuntimeError(f"OpenAI stream failed: {exc}") from exc
