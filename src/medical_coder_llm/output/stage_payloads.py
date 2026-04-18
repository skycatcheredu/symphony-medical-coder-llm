from __future__ import annotations

from typing import Any

from medical_coder_llm.types import (
    CandidateSelection,
    ClinicalCandidate,
    EvidenceSpan,
    FinalCode,
    IndexedCandidate,
    OntologyEntry,
)


def evidence_span_to_json(span: EvidenceSpan) -> dict[str, Any]:
    return {
        "text": span.text,
        "startChar": span.start_char,
        "endChar": span.end_char,
        "reason": span.reason,
    }


def clinical_candidate_to_json(candidate: ClinicalCandidate) -> dict[str, Any]:
    return {
        "id": candidate.id,
        "category": candidate.category,
        "label": candidate.label,
        "confidence": candidate.confidence,
        "evidenceSpans": [evidence_span_to_json(s) for s in candidate.evidence_spans],
    }


def ontology_entry_to_json(entry: OntologyEntry) -> dict[str, Any]:
    return {
        "code": entry.code,
        "description": entry.description,
        "codingSystem": entry.coding_system,
        "category": entry.category,
        "searchTerms": list(entry.search_terms),
    }


def indexed_candidate_to_json(item: IndexedCandidate) -> dict[str, Any]:
    return {
        "candidateId": item.candidate_id,
        "candidateLabel": item.candidate_label,
        "category": item.category,
        "evidenceSpans": [evidence_span_to_json(s) for s in item.evidence_spans],
        "matchedCodes": [ontology_entry_to_json(e) for e in item.matched_codes],
    }


def candidate_selection_to_json(sel: CandidateSelection) -> dict[str, Any]:
    return {
        "candidateId": sel.candidate_id,
        "selectedCode": sel.selected_code,
        "rationale": sel.rationale,
        "confidence": sel.confidence,
    }


def final_code_to_json(code: FinalCode) -> dict[str, Any]:
    return {
        "code": code.code,
        "description": code.description,
        "codingSystem": code.coding_system,
        "category": code.category,
        "confidence": code.confidence,
        "rationale": code.rationale,
        "evidenceSpans": [evidence_span_to_json(s) for s in code.evidence_spans],
    }


def evidence_extraction_output(
    *,
    patient_summary: str,
    candidates: list[ClinicalCandidate],
    llm_json: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "patientSummary": patient_summary,
        "candidates": [clinical_candidate_to_json(c) for c in candidates],
        "llmJson": llm_json,
    }


def index_navigation_output(*, indexed: list[IndexedCandidate]) -> dict[str, Any]:
    return {"indexedCandidates": [indexed_candidate_to_json(i) for i in indexed]}


def tabular_validation_output(
    *,
    selections: list[CandidateSelection],
    llm_json: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "selections": [candidate_selection_to_json(s) for s in selections],
        "llmJson": llm_json,
    }


def code_reconciliation_output(*, final_codes: list[FinalCode]) -> dict[str, Any]:
    return {"finalCodes": [final_code_to_json(c) for c in final_codes]}
