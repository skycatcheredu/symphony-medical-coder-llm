from __future__ import annotations

from medical_coder_llm.ontology.search import search_ontology
from medical_coder_llm.types import ClinicalCandidate, IndexedCandidate, OntologyEntry


def run_index_navigation(
    candidates: list[ClinicalCandidate],
    ontology_entries: list[OntologyEntry],
) -> list[IndexedCandidate]:
    result: list[IndexedCandidate] = []
    for candidate in candidates:
        matched_codes = search_ontology(
            ontology_entries,
            candidate.label,
            category=candidate.category,
            limit=8,
        )
        result.append(
            IndexedCandidate(
                candidate_id=candidate.id,
                candidate_label=candidate.label,
                category=candidate.category,
                evidence_spans=candidate.evidence_spans,
                matched_codes=matched_codes,
            )
        )
    return result
