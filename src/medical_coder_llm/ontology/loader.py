from __future__ import annotations

from pathlib import Path

from medical_coder_llm.types import CodeCategory, CodingSystem, OntologyEntry

REQUIRED_HEADERS = ("code", "description", "codingSystem", "category", "searchTerms")


def _parse_csv_line(line: str) -> list[str]:
    cells: list[str] = []
    current = ""
    in_quotes = False
    i = 0
    while i < len(line):
        char = line[i]
        if char == '"':
            nxt = line[i + 1] if i + 1 < len(line) else None
            if in_quotes and nxt == '"':
                current += '"'
                i += 2
                continue
            in_quotes = not in_quotes
            i += 1
            continue
        if char == "," and not in_quotes:
            cells.append(current.strip())
            current = ""
            i += 1
            continue
        current += char
        i += 1
    cells.append(current.strip())
    return cells


def _assert_valid_category(value: str) -> CodeCategory:
    if value in ("diagnosis", "procedure"):
        return value  # type: ignore[return-value]
    raise ValueError(f"Invalid category in ontology row: {value}")


def _assert_valid_system(value: str) -> CodingSystem:
    if value in ("ICD-10-CM", "ICD-10-PCS", "CPT"):
        return value  # type: ignore[return-value]
    raise ValueError(f"Invalid coding system in ontology row: {value}")


def load_ontology_entries(csv_path: str | Path) -> list[OntologyEntry]:
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"Ontology CSV not found at: {csv_path}")

    raw = path.read_text(encoding="utf-8")
    lines = [
        line.strip()
        for line in raw.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if len(lines) < 2:
        raise ValueError(f"Ontology CSV at {csv_path} is empty or missing data rows.")

    header_line = lines[0]
    headers = _parse_csv_line(header_line)
    for expected in REQUIRED_HEADERS:
        if expected not in headers:
            raise ValueError(f"Ontology CSV is missing required header: {expected}")

    indices = {header: idx for idx, header in enumerate(headers)}

    def get_index(header: str) -> int:
        try:
            return indices[header]
        except KeyError as e:
            raise ValueError(f"Ontology CSV missing required index for header: {header}") from e

    code_index = get_index("code")
    description_index = get_index("description")
    coding_system_index = get_index("codingSystem")
    category_index = get_index("category")
    search_terms_index = get_index("searchTerms")

    entries: list[OntologyEntry] = []
    for row_line in lines[1:]:
        row = _parse_csv_line(row_line)
        if len(row) <= max(
            code_index,
            description_index,
            coding_system_index,
            category_index,
            search_terms_index,
        ):
            continue
        code = row[code_index] if code_index < len(row) else ""
        if not code:
            continue
        description = row[description_index] if description_index < len(row) else ""
        coding_system = _assert_valid_system(row[coding_system_index] if coding_system_index < len(row) else "")
        category = _assert_valid_category(row[category_index] if category_index < len(row) else "")
        raw_terms = row[search_terms_index] if search_terms_index < len(row) else ""
        search_terms = [t.strip().lower() for t in raw_terms.split(";") if t.strip()]

        entries.append(
            OntologyEntry(
                code=code,
                description=description,
                coding_system=coding_system,
                category=category,
                search_terms=search_terms,
            )
        )

    return entries
