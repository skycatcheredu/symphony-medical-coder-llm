from __future__ import annotations

import json

from medical_coder_llm.output.stage_payloads import evidence_span_to_json, final_code_to_json
from medical_coder_llm.types import CodingResult, EvidenceSpan, FinalCode, StageTrace


def _evidence_span(span: EvidenceSpan) -> dict[str, object]:
    return evidence_span_to_json(span)


def _final_code(code: FinalCode) -> dict[str, object]:
    return final_code_to_json(code)


def _stage_trace(stage: StageTrace) -> dict[str, object]:
    return {
        "stage": stage.stage,
        "summary": stage.summary,
        "metadata": stage.metadata,
        "startedAt": stage.started_at,
        "finishedAt": stage.finished_at,
        "stageOutput": stage.output,
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
