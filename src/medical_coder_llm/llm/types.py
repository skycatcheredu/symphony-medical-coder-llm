from __future__ import annotations

import json
import re
from typing import Any, Protocol, TypeVar

from medical_coder_llm.config.models import LlmProvider


class JsonSchemaHint:
    def __init__(self, name: str, schema: dict[str, Any]) -> None:
        self.name = name
        self.schema = schema


class LlmPromptRequest:
    def __init__(
        self,
        *,
        system: str,
        user: str,
        temperature: float | None = None,
        json_schema: JsonSchemaHint | None = None,
    ) -> None:
        self.system = system
        self.user = user
        self.temperature = temperature
        self.json_schema = json_schema


T = TypeVar("T")


class LlmClient(Protocol):
    provider: LlmProvider
    model: str

    def generate_text(self, request: LlmPromptRequest) -> str: ...

    def generate_json(self, request: LlmPromptRequest) -> Any: ...


def extract_json_payload(raw: str) -> str:
    code_fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, re.IGNORECASE)
    if code_fence_match and code_fence_match.group(1):
        return code_fence_match.group(1).strip()

    first_curly = raw.find("{")
    last_curly = raw.rfind("}")
    if first_curly >= 0 and last_curly > first_curly:
        return raw[first_curly : last_curly + 1]

    raise ValueError("Could not locate JSON payload in model response.")


def parse_json_response(raw: str) -> Any:
    payload = extract_json_payload(raw)
    return json.loads(payload)
