from __future__ import annotations

from datetime import datetime, timezone

from medical_coder_llm.llm.types import LlmClient
from medical_coder_llm.pipeline.stages.code_reconciliation import run_code_reconciliation
from medical_coder_llm.pipeline.stages.evidence_extraction import run_evidence_extraction
from medical_coder_llm.pipeline.stages.index_navigation import run_index_navigation
from medical_coder_llm.pipeline.stages.tabular_validation import run_tabular_validation
from medical_coder_llm.output.stage_payloads import (
    code_reconciliation_output,
    evidence_extraction_output,
    index_navigation_output,
    tabular_validation_output,
)
from medical_coder_llm.types import CodingResult, OntologyEntry, StageTrace


def _iso_utc(dt: datetime | None = None) -> str:
    base = dt if dt is not None else datetime.now(timezone.utc)
    return base.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def run_coding_pipeline(
    *,
    note_text: str,
    llm: LlmClient,
    ontology_entries: list[OntologyEntry],
) -> CodingResult:
    trace: list[StageTrace] = []

    evidence_start = datetime.now(timezone.utc)
    evidence, evidence_llm = run_evidence_extraction(llm, note_text)
    trace.append(
        StageTrace(
            stage="evidence_extraction",
            summary=f"Extracted {len(evidence.candidates)} codable candidates.",
            metadata={"candidateCount": len(evidence.candidates)},
            started_at=_iso_utc(evidence_start),
            finished_at=_iso_utc(),
            output=evidence_extraction_output(
                patient_summary=evidence.patient_summary,
                candidates=evidence.candidates,
                llm_json=evidence_llm,
            ),
        )
    )

    index_start = datetime.now(timezone.utc)
    indexed = run_index_navigation(evidence.candidates, ontology_entries)
    trace.append(
        StageTrace(
            stage="index_navigation",
            summary=f"Generated candidate code options for {len(indexed)} findings.",
            metadata={
                "findingsWithOptions": sum(1 for item in indexed if len(item.matched_codes) > 0),
            },
            started_at=_iso_utc(index_start),
            finished_at=_iso_utc(),
            output=index_navigation_output(indexed=indexed),
        )
    )

    tabular_start = datetime.now(timezone.utc)
    selections, tabular_llm = run_tabular_validation(llm, note_text, indexed)
    trace.append(
        StageTrace(
            stage="tabular_validation",
            summary=f"Validated {len(selections)} candidate selections.",
            metadata={
                "selectedCount": sum(1 for item in selections if len(item.selected_code) > 0),
            },
            started_at=_iso_utc(tabular_start),
            finished_at=_iso_utc(),
            output=tabular_validation_output(selections=selections, llm_json=tabular_llm),
        )
    )

    reconcile_start = datetime.now(timezone.utc)
    final_codes = run_code_reconciliation(indexed, selections)
    trace.append(
        StageTrace(
            stage="code_reconciliation",
            summary=f"Reconciled to {len(final_codes)} final codes.",
            metadata={
                "diagnosisCount": sum(1 for code in final_codes if code.category == "diagnosis"),
                "procedureCount": sum(1 for code in final_codes if code.category == "procedure"),
            },
            started_at=_iso_utc(reconcile_start),
            finished_at=_iso_utc(),
            output=code_reconciliation_output(final_codes=final_codes),
        )
    )

    return CodingResult(
        patient_summary=evidence.patient_summary,
        diagnosis_codes=[c for c in final_codes if c.category == "diagnosis"],
        procedure_codes=[c for c in final_codes if c.category == "procedure"],
        stage_trace=trace,
        generated_at=_iso_utc(),
        provider=llm.provider,
        model=llm.model,
    )
