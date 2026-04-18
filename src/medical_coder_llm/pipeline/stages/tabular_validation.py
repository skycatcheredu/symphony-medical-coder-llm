from __future__ import annotations

from typing import Any

from medical_coder_llm.llm.types import LlmClient, LlmPromptRequest
from medical_coder_llm.types import CandidateSelection, IndexedCandidate


def _build_candidate_context(indexed: list[IndexedCandidate]) -> str:
    blocks: list[str] = []
    for candidate in indexed:
        options = "\n".join(
            f"{code.code} | {code.description} | {code.coding_system}" for code in candidate.matched_codes
        )
        blocks.append(
            "\n".join(
                [
                    f"Candidate: {candidate.candidate_id}",
                    f"Category: {candidate.category}",
                    f"Label: {candidate.candidate_label}",
                    "Options:",
                    options or "(none)",
                ]
            )
        )
    return "\n\n---\n\n".join(blocks)


def run_tabular_validation(
    llm: LlmClient,
    note_text: str,
    indexed: list[IndexedCandidate],
) -> list[CandidateSelection]:
    if not indexed:
        return []

    response: dict[str, Any] | None = None
    try:
        response = llm.generate_json(
            LlmPromptRequest(
                system=(
                    "You are a medical coding validator. For each candidate, choose the most "
                    "specific correct code from provided options. If no option is valid, "
                    "selectedCode must be empty string."
                ),
                user=(
                    f"Clinical note:\n{note_text}\n\nCandidates and options:\n"
                    f"{_build_candidate_context(indexed)}\n\nReturn JSON with selections."
                ),
                temperature=0.1,
            )
        )
        if not isinstance(response, dict):
            response = None
    except Exception:
        response = None

    raw_selections = response.get("selections") if isinstance(response, dict) else None
    selections_list = raw_selections if isinstance(raw_selections, list) else []
    normalized: list[CandidateSelection] = []
    for selection in selections_list:
        if not isinstance(selection, dict):
            continue
        cid = str(selection.get("candidateId") or "")
        sel_code = str(selection.get("selectedCode") or "").strip()
        raw_conf = selection.get("confidence")
        try:
            conf_val = float(raw_conf) if raw_conf is not None else 0.5
        except (TypeError, ValueError):
            conf_val = 0.5
        normalized.append(
            CandidateSelection(
                candidate_id=cid,
                selected_code=sel_code,
                rationale=str(selection.get("rationale") or ""),
                confidence=max(0.0, min(1.0, conf_val)),
            )
        )

    by_candidate: dict[str, CandidateSelection] = {s.candidate_id: s for s in normalized if s.candidate_id}
    for candidate in indexed:
        if candidate.candidate_id in by_candidate:
            continue
        first_option = candidate.matched_codes[0] if candidate.matched_codes else None
        if not first_option:
            continue
        by_candidate[candidate.candidate_id] = CandidateSelection(
            candidate_id=candidate.candidate_id,
            selected_code=first_option.code,
            rationale="Fallback selection from top ontology index match.",
            confidence=0.35,
        )

    return [v for v in by_candidate.values() if v.candidate_id]
