from __future__ import annotations

import time
import json
import logging
from typing import AsyncGenerator, Optional

import httpx

from .base import LLMProvider, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)

SUPPORTED_MODELS = [
    "llama3",
    "mistral",
    "codellama",
    "phi3",
]

DEFAULT_BASE_URL = "http://localhost:11434"


class LocalProvider(LLMProvider):

    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=120.0)

    def list_models(self) -> list[str]:
        return list(SUPPORTED_MODELS)

    async def complete(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        start = time.monotonic()
        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            latency = (time.monotonic() - start) * 1000

            data = response.json()
            content = data.get("message", {}).get("content", "")
            tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
            done = data.get("done", True)

            self._log_call(model, latency, tokens)

            return LLMResponse(
                content=content,
                model=data.get("model", model),
                tokens_used=tokens,
                finish_reason="stop" if done else "length",
                latency_ms=latency,
            )
        except httpx.HTTPStatusError as exc:
            latency = (time.monotonic() - start) * 1000
            self._log_call(model, latency, 0, success=False)
            raise RuntimeError(f"Ollama HTTP error {exc.response.status_code}: {exc}") from exc
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Ensure Ollama is running."
            )
        except Exception as exc:
            latency = (time.monotonic() - start) * 1000
            self._log_call(model, latency, 0, success=False)
            raise RuntimeError(f"Local LLM request failed: {exc}") from exc

    async def stream(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        start = time.monotonic()
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

            latency = (time.monotonic() - start) * 1000
            self._log_call(model, latency, 0)
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Ensure Ollama is running."
            )
        except Exception as exc:
            latency = (time.monotonic() - start) * 1000
            self._log_call(model, latency, 0, success=False)
            raise RuntimeError(f"Local LLM stream failed: {exc}") from exc
