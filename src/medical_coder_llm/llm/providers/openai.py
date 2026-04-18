from __future__ import annotations

from typing import Any

import httpx

from medical_coder_llm.config.models import LlmProvider
from medical_coder_llm.llm.types import LlmPromptRequest, parse_json_response


class OpenAiClient:
    provider: LlmProvider = "openai"

    def __init__(
        self,
        model: str,
        api_key: str,
        http: httpx.Client,
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._http = http
        self._base_url = base_url.rstrip("/")

    def generate_text(self, request: LlmPromptRequest) -> str:
        response = self._http.post(
            f"{self._base_url}/responses",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            json={
                "model": self.model,
                "temperature": request.temperature if request.temperature is not None else 0.2,
                "input": [
                    {"role": "system", "content": request.system},
                    {"role": "user", "content": request.user},
                ],
            },
        )
        if not response.is_success:
            raise RuntimeError(f"OpenAI request failed ({response.status_code}): {response.text}")

        payload: dict[str, Any] = response.json()
        output = payload.get("output") or []
        parts: list[str] = []
        for segment in output:
            for item in segment.get("content") or []:
                if item.get("type") in ("output_text", "text"):
                    parts.append(str(item.get("text") or ""))
        text = "\n".join(parts).strip()
        if not text:
            raise RuntimeError("OpenAI response did not contain text output.")
        return text

    def generate_json(self, request: LlmPromptRequest) -> Any:
        system_with_json_rule = (
            f"{request.system}\n\nReturn ONLY valid JSON. Do not include markdown code fences."
        )
        raw = self.generate_text(
            LlmPromptRequest(
                system=system_with_json_rule,
                user=request.user,
                temperature=request.temperature,
                json_schema=request.json_schema,
            )
        )
        try:
            return parse_json_response(raw)
        except Exception:
            repaired = self.generate_text(
                LlmPromptRequest(
                    system="You repair invalid JSON. Return valid JSON only.",
                    user=f"Repair this text into strict JSON while preserving data:\n{raw}",
                    temperature=0,
                )
            )
            return parse_json_response(repaired)


def _message_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts).strip()
    if content is None:
        return ""
    return str(content).strip()


class LmStudioClient:
    """OpenAI-compatible `/v1/chat/completions` (e.g. LM Studio local server)."""

    provider: LlmProvider = "lm_studio"

    def __init__(
        self,
        model: str,
        api_key: str,
        http: httpx.Client,
        base_url: str,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._http = http
        self._base_url = base_url.rstrip("/")

    def generate_text(self, request: LlmPromptRequest) -> str:
        response = self._http.post(
            f"{self._base_url}/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            json={
                "model": self.model,
                "temperature": request.temperature if request.temperature is not None else 0.2,
                "messages": [
                    {"role": "system", "content": request.system},
                    {"role": "user", "content": request.user},
                ],
            },
        )
        if not response.is_success:
            raise RuntimeError(
                f"LM Studio / chat-completions request failed ({response.status_code}): {response.text}",
            )

        payload: dict[str, Any] = response.json()
        choices = payload.get("choices") or []
        if not choices:
            raise RuntimeError("Chat-completions response contained no choices.")
        message = choices[0].get("message") or {}
        text = _message_content_to_text(message.get("content"))
        if not text:
            raise RuntimeError("Chat-completions response did not contain message content.")
        return text

    def generate_json(self, request: LlmPromptRequest) -> Any:
        system_with_json_rule = (
            f"{request.system}\n\nReturn ONLY valid JSON. Do not include markdown code fences."
        )
        raw = self.generate_text(
            LlmPromptRequest(
                system=system_with_json_rule,
                user=request.user,
                temperature=request.temperature,
                json_schema=request.json_schema,
            )
        )
        try:
            return parse_json_response(raw)
        except Exception:
            repaired = self.generate_text(
                LlmPromptRequest(
                    system="You repair invalid JSON. Return valid JSON only.",
                    user=f"Repair this text into strict JSON while preserving data:\n{raw}",
                    temperature=0,
                )
            )
            return parse_json_response(repaired)
