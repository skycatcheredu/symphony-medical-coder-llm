from __future__ import annotations

from typing import Literal

LlmProvider = Literal["openai", "gemini"]


class ModelConfig:
    def __init__(self, provider: LlmProvider, model: str) -> None:
        self.provider = provider
        self.model = model


DEFAULT_MODEL_CONFIG = ModelConfig(
    provider="gemini",
    model="gemini-3.1-flash",
)

PROVIDER_MODEL_OPTIONS: dict[LlmProvider, list[str]] = {
    "openai": ["gpt-5.1-mini", "gpt-5.1-mini", "gpt-5.1-mini"],
    "gemini": ["gemini-3.1-flash", "gemini-2.5-flash", "gemini-1.5-flash"],
}


def resolve_model_config(
    *,
    provider: LlmProvider | None = None,
    model: str | None = None,
) -> ModelConfig:
    return ModelConfig(
        provider=provider if provider is not None else DEFAULT_MODEL_CONFIG.provider,
        model=model if model is not None else DEFAULT_MODEL_CONFIG.model,
    )
