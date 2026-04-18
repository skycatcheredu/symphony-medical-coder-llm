from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from medical_coder_llm.config.models import LlmProvider
from medical_coder_llm.llm.types import LlmPromptRequest, parse_json_response


class GeminiClient:
    provider: LlmProvider = "gemini"

    def __init__(
        self,
        model: str,
        api_key: str,
        http: httpx.Client,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta/models",
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._http = http
        self._base_url = base_url.rstrip("/")

    def generate_text(self, request: LlmPromptRequest) -> str:
        url = (
            f"{self._base_url}/{quote(self.model, safe='')}:generateContent"
            f"?key={quote(self._api_key, safe='')}"
        )
        response = self._http.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "systemInstruction": {"parts": [{"text": request.system}]},
                "generationConfig": {
                    "temperature": request.temperature if request.temperature is not None else 0.2,
                },
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": request.user}],
                    }
                ],
            },
        )
        if not response.is_success:
            raise RuntimeError(f"Gemini request failed ({response.status_code}): {response.text}")

        payload: dict[str, Any] = response.json()
        candidates = payload.get("candidates") or []
        parts_text: list[str] = []
        if candidates:
            for part in (candidates[0].get("content") or {}).get("parts") or []:
                parts_text.append(str(part.get("text") or ""))
        text = "\n".join(parts_text).strip()
        if not text:
            raise RuntimeError("Gemini response did not contain text output.")
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
