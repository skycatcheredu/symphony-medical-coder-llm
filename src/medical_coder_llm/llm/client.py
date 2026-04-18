from __future__ import annotations

import os

import httpx

from medical_coder_llm.config.models import ModelConfig, is_openai_cloud_base
from medical_coder_llm.llm.providers.gemini import GeminiClient
from medical_coder_llm.llm.providers.openai import LmStudioClient, OpenAiClient
from medical_coder_llm.llm.types import LlmClient


def build_llm_client(config: ModelConfig, http: httpx.Client) -> LlmClient:
    if config.provider == "openai":
        base = (config.base_url or "").rstrip("/")
        if not base:
            raise RuntimeError("OpenAI provider requires a base URL (internal config error).")
        if is_openai_cloud_base(base):
            api_key = os.environ.get("OPENAI_API_KEY", "").strip()
            if not api_key:
                raise RuntimeError(
                    "Missing OPENAI_API_KEY environment variable for OpenAI provider.",
                )
            return OpenAiClient(config.model, api_key, http, base_url=base)
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
