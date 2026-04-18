from __future__ import annotations

import httpx

from medical_coder_llm.config.models import LlmProvider, resolve_model_config
from medical_coder_llm.llm.client import build_llm_client
from medical_coder_llm.ontology.loader import load_ontology_entries
from medical_coder_llm.output.format import format_result_as_json
from medical_coder_llm.pipeline.orchestrator import run_coding_pipeline


def run_coding_to_json(
    note_text: str,
    *,
    ontology_path: str,
    provider: str | None = None,
    model: str | None = None,
) -> str:
    """Run the full coding pipeline and return formatted JSON string.

    Raises:
        ValueError: Empty note, invalid provider, or ontology load failure.
    """
    note = note_text.strip()
    if not note:
        raise ValueError("Patient note is empty.")

    if provider is not None and provider not in ("openai", "gemini"):
        raise ValueError("Unsupported provider. Use openai or gemini.")

    llm_provider: LlmProvider | None = provider  # type: ignore[assignment]

    try:
        ontology_entries = load_ontology_entries(ontology_path)
    except (OSError, ValueError) as e:
        raise ValueError(str(e)) from e

    model_config = resolve_model_config(provider=llm_provider, model=model)

    with httpx.Client(timeout=120.0) as http:
        llm = build_llm_client(model_config, http)
        result = run_coding_pipeline(
            note_text=note,
            llm=llm,
            ontology_entries=ontology_entries,
        )

    return format_result_as_json(result)
