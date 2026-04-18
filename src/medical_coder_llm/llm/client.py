from __future__ import annotations

import os

import httpx

from medical_coder_llm.config.models import ModelConfig
from medical_coder_llm.llm.providers.gemini import GeminiClient
from medical_coder_llm.llm.providers.openai import LmStudioClient, OpenAiClient
from medical_coder_llm.llm.types import LlmClient


def build_llm_client(config: ModelConfig, http: httpx.Client) -> LlmClient:
    if config.provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "Missing OPENAI_API_KEY environment variable for OpenAI provider.",
            )
        base = config.base_url or "https://api.openai.com/v1"
        return OpenAiClient(config.model, api_key, http, base_url=base)

    if config.provider == "lm_studio":
        base = config.base_url
        if not base:
            raise RuntimeError("LM Studio provider requires OPEN_AI_URL (base URL including /v1).")
        api_key = os.environ.get("OPENAI_API_KEY", "").strip() or "lm-studio"
        return LmStudioClient(config.model, api_key, http, base_url=base)

    if config.provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY environment variable for Gemini provider.",
            )
        return GeminiClient(config.model, api_key, http)

    raise RuntimeError(f"Unsupported provider: {config.provider!r}")
