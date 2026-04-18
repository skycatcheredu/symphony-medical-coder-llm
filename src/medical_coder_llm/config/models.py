from __future__ import annotations

import os
from typing import Literal

LlmProvider = Literal["openai", "gemini"]

_DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"


def is_openai_cloud_base(base_url: str) -> bool:
    """True when the resolved base is the default OpenAI cloud API (uses /responses)."""
    return base_url.rstrip("/") == _DEFAULT_OPENAI_BASE.rstrip("/")


class ModelConfig:
    def __init__(
        self,
        provider: LlmProvider,
        model: str,
        *,
        base_url: str | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.base_url = base_url


def resolve_model_config() -> ModelConfig:
    """Load LLM settings from environment. See `.env.example` for variable names."""
    raw_provider = os.environ.get("MODEL_PROVIDER", "").strip().lower()
    # Backward compat: lm_studio was OpenAI-compatible; use openai + OPEN_AI_URL.
    if raw_provider == "lm_studio":
        raw_provider = "openai"
    if not raw_provider:
        raise RuntimeError(
            "Missing MODEL_PROVIDER. Set it in your environment or `.env` "
            "(e.g. gemini or openai). See `.env.example`.",
        )
    if raw_provider not in ("openai", "gemini"):
        raise RuntimeError(
            f"Invalid MODEL_PROVIDER: {raw_provider!r}. Use gemini or openai.",
        )
    provider: LlmProvider = raw_provider

    model = os.environ.get("MODEL_NAME", "").strip()
    if not model:
        raise RuntimeError(
            "Missing MODEL_NAME. Set it in your environment or `.env`. See `.env.example`.",
        )

    if provider == "gemini":
        return ModelConfig(provider=provider, model=model, base_url=None)

    base = os.environ.get("OPEN_AI_URL", "").strip().rstrip("/")
    if not base:
        base = _DEFAULT_OPENAI_BASE.rstrip("/")
    return ModelConfig(provider=provider, model=model, base_url=base)
