from __future__ import annotations

import os

import httpx

from medical_coder_llm.config.models import ModelConfig
from medical_coder_llm.llm.providers.gemini import GeminiClient
from medical_coder_llm.llm.providers.openai import OpenAiClient
from medical_coder_llm.llm.types import LlmClient


def build_llm_client(config: ModelConfig, http: httpx.Client) -> LlmClient:
    if config.provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Missing OPENAI_API_KEY environment variable for OpenAI provider.",
            )
        return OpenAiClient(config.model, api_key, http)

    if config.provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY environment variable for Gemini provider.",
            )
        return GeminiClient(config.model, api_key, http)

    raise RuntimeError(f"Unsupported provider: {config.provider!r}")
