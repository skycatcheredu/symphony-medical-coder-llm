from __future__ import annotations

import os
from typing import Literal

LlmProvider = Literal["openai", "gemini", "lm_studio"]

_DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"


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
    if not raw_provider:
        raise RuntimeError(
            "Missing MODEL_PROVIDER. Set it in your environment or `.env` "
            "(e.g. gemini, openai, lm_studio). See `.env.example`.",
        )
    if raw_provider not in ("openai", "gemini", "lm_studio"):
        raise RuntimeError(
            f"Invalid MODEL_PROVIDER: {raw_provider!r}. Use gemini, openai, or lm_studio.",
        )
    provider: LlmProvider = raw_provider  # type: ignore[assignment]

    model = os.environ.get("MODEL_NAME", "").strip()
    if not model:
        raise RuntimeError(
            "Missing MODEL_NAME. Set it in your environment or `.env`. See `.env.example`.",
        )

    if provider == "gemini":
        return ModelConfig(provider=provider, model=model, base_url=None)

    base = os.environ.get("OPEN_AI_URL", "").strip().rstrip("/")
    if provider == "lm_studio":
        if not base:
            raise RuntimeError(
                "MODEL_PROVIDER=lm_studio requires OPEN_AI_URL "
                "(e.g. http://127.0.0.1:1234/v1). See `.env.example`.",
            )
        return ModelConfig(provider=provider, model=model, base_url=base)

    # openai
    if not base:
        base = _DEFAULT_OPENAI_BASE.rstrip("/")
    return ModelConfig(provider=provider, model=model, base_url=base)
