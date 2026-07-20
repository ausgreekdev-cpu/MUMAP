from __future__ import annotations

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

logger = logging.getLogger(__name__)


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int = 0
    finish_reason: str = "stop"
    latency_ms: float = 0.0


class LLMProvider(ABC):

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        ...

    @abstractmethod
    def list_models(self) -> list[str]:
        ...

    def count_tokens(self, text: str) -> int:
        return len(text) // 4

    def _log_call(self, model: str, latency_ms: float, tokens: int, success: bool = True):
        status = "success" if success else "error"
        logger.info(
            "llm_call",
            extra={
                "provider": self.__class__.__name__,
                "model": model,
                "latency_ms": round(latency_ms, 2),
                "tokens": tokens,
                "status": status,
            },
        )
