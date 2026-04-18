from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

CodingSystem = Literal["ICD-10-CM", "ICD-10-PCS", "CPT"]
CodeCategory = Literal["diagnosis", "procedure"]
StageName = Literal[
    "evidence_extraction",
    "index_navigation",
    "tabular_validation",
    "code_reconciliation",
]


@dataclass
class PatientInput:
    source_path: str
    text: str


@dataclass
class EvidenceSpan:
    text: str
    start_char: int
    end_char: int
    reason: str


@dataclass
class ClinicalCandidate:
    id: str
    category: CodeCategory
    label: str
    confidence: float
    evidence_spans: list[EvidenceSpan]


@dataclass
class OntologyEntry:
    code: str
    description: str
    coding_system: CodingSystem
    category: CodeCategory
    search_terms: list[str]


@dataclass
class IndexedCandidate:
    candidate_id: str
    candidate_label: str
    category: CodeCategory
    evidence_spans: list[EvidenceSpan]
    matched_codes: list[OntologyEntry]


@dataclass
class CandidateSelection:
    candidate_id: str
    selected_code: str
    rationale: str
    confidence: float


@dataclass
class FinalCode:
    code: str
    description: str
    coding_system: CodingSystem
    category: CodeCategory
    confidence: float
    rationale: str
    evidence_spans: list[EvidenceSpan]


@dataclass
class StageTrace:
    stage: StageName
    summary: str
    metadata: dict[str, Any]
    started_at: str
    finished_at: str
    output: dict[str, Any] = field(default_factory=dict)


@dataclass
class CodingResult:
    patient_summary: str
    diagnosis_codes: list[FinalCode]
    procedure_codes: list[FinalCode]
    stage_trace: list[StageTrace]
    generated_at: str
    provider: str
    model: str
