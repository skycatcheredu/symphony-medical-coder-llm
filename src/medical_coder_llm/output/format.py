from __future__ import annotations

import json

from medical_coder_llm.types import CodingResult, EvidenceSpan, FinalCode, StageTrace


def _evidence_span(span: EvidenceSpan) -> dict[str, object]:
    return {
        "text": span.text,
        "startChar": span.start_char,
        "endChar": span.end_char,
        "reason": span.reason,
    }


def _final_code(code: FinalCode) -> dict[str, object]:
    return {
        "code": code.code,
        "description": code.description,
        "codingSystem": code.coding_system,
        "category": code.category,
        "confidence": code.confidence,
        "rationale": code.rationale,
        "evidenceSpans": [_evidence_span(s) for s in code.evidence_spans],
    }


def _stage_trace(stage: StageTrace) -> dict[str, object]:
    return {
        "stage": stage.stage,
        "summary": stage.summary,
        "metadata": stage.metadata,
        "startedAt": stage.started_at,
        "finishedAt": stage.finished_at,
    }


def format_result_as_json(result: CodingResult) -> str:
    payload: dict[str, object] = {
        "patientSummary": result.patient_summary,
        "diagnosisCodes": [_final_code(c) for c in result.diagnosis_codes],
        "procedureCodes": [_final_code(c) for c in result.procedure_codes],
        "stageTrace": [_stage_trace(s) for s in result.stage_trace],
        "generatedAt": result.generated_at,
        "provider": result.provider,
        "model": result.model,
    }
    return json.dumps(payload, indent=2)
