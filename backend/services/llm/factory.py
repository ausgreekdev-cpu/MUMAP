from __future__ import annotations

import logging
from typing import Optional

from .base import LLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .local_provider import LocalProvider

logger = logging.getLogger(__name__)

PROVIDERS: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "local": LocalProvider,
}


def get_llm_provider(provider: str, config: Optional[dict] = None) -> LLMProvider:
    config = config or {}

    provider_cls = PROVIDERS.get(provider.lower())
    if provider_cls is None:
        available = ", ".join(PROVIDERS.keys())
        raise ValueError(f"Unknown LLM provider '{provider}'. Available: {available}")

    try:
        if provider == "openai":
            return OpenAIProvider(
                api_key=config.get("api_key", ""),
                organization_id=config.get("organization_id"),
            )
        elif provider == "anthropic":
            return AnthropicProvider(
                api_key=config.get("api_key", ""),
            )
        elif provider == "local":
            return LocalProvider(
                base_url=config.get("base_url", "http://localhost:11434"),
            )
    except ImportError as exc:
        logger.error("provider_import_error provider=%s error=%s", provider, exc)
        raise
    except Exception as exc:
        logger.error("provider_init_error provider=%s error=%s", provider, exc)
        raise

    raise ValueError(f"Provider '{provider}' initialization not implemented")
