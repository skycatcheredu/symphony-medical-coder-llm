from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from medical_coder_llm.llm.types import LlmClient, LlmPromptRequest
from medical_coder_llm.types import ClinicalCandidate, CodeCategory, EvidenceSpan


@dataclass
class EvidenceExtractionResult:
    patient_summary: str
    candidates: list[ClinicalCandidate]


def _build_fallback_summary(note_text: str) -> str:
    clean = re.sub(r"\s+", " ", note_text).strip()
    return clean[:240]


def _build_fallback_candidates(note_text: str) -> list[dict[str, Any]]:
    lines = [ln.strip() for ln in note_text.splitlines() if ln.strip()]
    result: list[dict[str, Any]] = []
    for line in lines:
        lower = line.lower()
        category: CodeCategory = (
            "procedure"
            if ("procedure" in lower or "performed" in lower or "visit" in lower)
            else "diagnosis"
        )
        label = re.sub(r"^([a-z ]+):", "", line, flags=re.IGNORECASE).rstrip(".").strip()
        if not label:
            continue
        start_char = note_text.lower().find(label.lower())
        end_char = start_char + len(label) if start_char >= 0 else 0
        result.append(
            {
                "id": f"fallback_{len(result) + 1}",
                "category": category,
                "label": label,
                "confidence": 0.45,
                "evidenceSpans": [
                    {
                        "text": label,
                        "startChar": max(0, start_char),
                        "endChar": max(0, end_char),
                        "reason": "Heuristic fallback extraction from note line.",
                    }
                ],
            }
        )
        if len(result) >= 10:
            break
    return result


def run_evidence_extraction(llm: LlmClient, note_text: str) -> EvidenceExtractionResult:
    response: dict[str, Any] | None = None
    try:
        response = llm.generate_json(
            LlmPromptRequest(
                system=(
                    "You are an expert medical coding pre-processor. Extract codable diagnoses "
                    "and procedures with direct evidence spans from the clinical note."
                ),
                user=f"Clinical note:\n{note_text}\n\nReturn JSON with patientSummary and candidates.",
                temperature=0.1,
            )
        )
        if not isinstance(response, dict):
            response = None
    except Exception:
        response = None

    fallback_candidates = _build_fallback_candidates(note_text)
    raw_list = response.get("candidates") if isinstance(response, dict) else None
    raw_candidates = raw_list if isinstance(raw_list, list) else fallback_candidates

    candidates: list[ClinicalCandidate] = []
    for index, candidate in enumerate(raw_candidates):
        if not isinstance(candidate, dict):
            continue
        raw_spans = candidate.get("evidenceSpans")
        spans_in = raw_spans if isinstance(raw_spans, list) else []
        evidence_spans: list[EvidenceSpan] = []
        for span in spans_in:
            if not isinstance(span, dict):
                continue
            evidence_spans.append(
                EvidenceSpan(
                    text=str(span.get("text") or ""),
                    start_char=int(span.get("startChar") or 0),
                    end_char=int(span.get("endChar") or 0),
                    reason=str(span.get("reason") or "model extracted evidence"),
                )
            )
        cat_raw = candidate.get("category")
        category: CodeCategory = "procedure" if cat_raw == "procedure" else "diagnosis"
        raw_conf = candidate.get("confidence")
        try:
            conf_val = float(raw_conf) if raw_conf is not None else 0.5
        except (TypeError, ValueError):
            conf_val = 0.5
        candidates.append(
            ClinicalCandidate(
                id=str(candidate.get("id") or f"candidate_{index + 1}"),
                category=category,
                label=str(candidate.get("label") or "unspecified finding"),
                confidence=max(0.0, min(1.0, conf_val)),
                evidence_spans=evidence_spans,
            )
        )

    patient_summary = ""
    if isinstance(response, dict) and response.get("patientSummary") is not None:
        patient_summary = str(response.get("patientSummary") or "")
    if not patient_summary:
        patient_summary = _build_fallback_summary(note_text)

    return EvidenceExtractionResult(patient_summary=patient_summary, candidates=candidates)
