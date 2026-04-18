from __future__ import annotations

from medical_coder_llm.types import CodeCategory, OntologyEntry


def _score_entry(entry: OntologyEntry, query: str) -> int:
    q = query.strip().lower()
    description = entry.description.lower()
    score = 0
    if entry.code.lower() == q:
        score += 10
    if q in description:
        score += 6
    if any(term == q for term in entry.search_terms):
        score += 7
    if any(term in q or q in term for term in entry.search_terms):
        score += 4
    query_words = [w for w in q.split() if w]
    for word in query_words:
        if word in description:
            score += 1
        if any(word in term for term in entry.search_terms):
            score += 1
    return score


def search_ontology(
    entries: list[OntologyEntry],
    query: str,
    *,
    category: CodeCategory,
    limit: int = 8,
) -> list[OntologyEntry]:
    scored = [
        (entry, _score_entry(entry, query))
        for entry in entries
        if entry.category == category and _score_entry(entry, query) > 0
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [e for e, _ in scored[:limit]]
