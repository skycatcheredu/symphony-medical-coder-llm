from __future__ import annotations

from medical_coder_llm.types import CandidateSelection, FinalCode, IndexedCandidate


def _is_more_specific_code(new_code: str, old_code: str) -> bool:
    if new_code == old_code:
        return False
    return len(new_code) > len(old_code)


def run_code_reconciliation(
    indexed: list[IndexedCandidate],
    selections: list[CandidateSelection],
) -> list[FinalCode]:
    by_candidate_id: dict[str, IndexedCandidate] = {item.candidate_id: item for item in indexed}
    final_by_code: dict[str, FinalCode] = {}

    for selection in selections:
        if not selection.selected_code:
            continue
        indexed_item = by_candidate_id.get(selection.candidate_id)
        if not indexed_item:
            continue
        matched = next(
            (entry for entry in indexed_item.matched_codes if entry.code == selection.selected_code),
            None,
        )
        if not matched:
            continue
        proposed = FinalCode(
            code=matched.code,
            description=matched.description,
            coding_system=matched.coding_system,
            category=matched.category,
            confidence=selection.confidence,
            rationale=selection.rationale,
            evidence_spans=indexed_item.evidence_spans,
        )
        existing = final_by_code.get(proposed.code)
        if not existing:
            final_by_code[proposed.code] = proposed
            continue
        if proposed.confidence > existing.confidence:
            final_by_code[proposed.code] = proposed

    sorted_codes = sorted(final_by_code.values(), key=lambda c: c.code)
    resolved: list[FinalCode] = []
    for code in sorted_codes:
        duplicate_family_index = next(
            (
                idx
                for idx, existing in enumerate(resolved)
                if (
                    (code.code.startswith(existing.code) or existing.code.startswith(code.code))
                    and code.category == existing.category
                    and code.coding_system == existing.coding_system
                )
            ),
            -1,
        )
        if duplicate_family_index == -1:
            resolved.append(code)
            continue
        existing = resolved[duplicate_family_index]
        if _is_more_specific_code(code.code, existing.code) or code.confidence > existing.confidence:
            resolved[duplicate_family_index] = code

    return resolved
