#!/usr/bin/env python3
"""Derive searchTerms from ontology description text (heuristic, offline).

Typical flow after refreshing CMS codes:
  uv run python scripts/build_ontology_cms.py
  uv run python scripts/enrich_ontology_search_terms.py --in-place

Or write to a new file (default):
  uv run python scripts/enrich_ontology_search_terms.py \\
    --input data/ontology/codes.csv --output data/ontology/codes.enriched.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import tempfile
from pathlib import Path

REQUIRED_HEADERS = ("code", "description", "codingSystem", "category", "searchTerms")

DEFAULT_INPUT = Path("data/ontology/codes.csv")
DEFAULT_OUTPUT = Path("data/ontology/codes.enriched.csv")

# Fragments consisting only of these (after tokenizing) are dropped.
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "with",
        "without",
        "by",
        "from",
        "as",
        "at",
        "into",
        "via",
        "per",
        "other",
        "unspecified",
        "specified",
        "not",
        "elsewhere",
        "classified",
        "acute",
        "chronic",
        "due",
        "use",
        "additional",
        "code",
        "encounter",
        "initial",
        "subsequent",
        "sequela",
    },
)

_SPLIT_RE = re.compile(r",|;|/|\||\(|\)")
_WORD_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def _normalize_fragment(s: str) -> str:
    t = " ".join(s.split())
    return t.strip().lower()


def _is_noise_fragment(fragment: str) -> bool:
    if len(fragment) < 3:
        return True
    words = [w.lower() for w in _WORD_RE.findall(fragment)]
    if not words:
        return True
    return all(w in _STOPWORDS for w in words)


def _split_description(description: str) -> list[str]:
    parts: list[str] = []
    for raw in _SPLIT_RE.split(description):
        frag = _normalize_fragment(raw)
        if frag and not _is_noise_fragment(frag):
            parts.append(frag)
    return parts


def _ngram_candidates(description: str, *, max_words: int = 8) -> list[str]:
    first_clause = description.split(",")[0].strip()
    words = [w.lower() for w in _WORD_RE.findall(first_clause)][:max_words]
    out: list[str] = []
    for w in words:
        if len(w) >= 3 and w not in _STOPWORDS:
            out.append(w)
    for i in range(len(words) - 1):
        a, b = words[i], words[i + 1]
        if a in _STOPWORDS and b in _STOPWORDS:
            continue
        phrase = f"{a} {b}"
        if len(phrase) >= 5:
            out.append(phrase)
    return out


def _terms_for_row(
    description: str,
    *,
    max_terms: int,
    max_fragment_len: int,
    include_ngrams: bool,
) -> str:
    if not description.strip():
        return ""

    candidates: list[str] = []
    seen: set[str] = set()

    def add_many(items: list[str]) -> None:
        for item in items:
            item = item.strip()
            if len(item) > max_fragment_len:
                snippet = item[:max_fragment_len]
                cut = snippet.rfind(" ")
                item = snippet[:cut].strip() if cut >= 3 else snippet.strip()
                if len(item) < 3:
                    continue
            if item in seen or _is_noise_fragment(item):
                continue
            seen.add(item)
            candidates.append(item)

    add_many(_split_description(description))
    if include_ngrams:
        add_many(_ngram_candidates(description))

    if not candidates:
        return ""

    # Prefer longer fragments first (more specific); preserve discovery order for ties.
    order = sorted(range(len(candidates)), key=lambda i: (-len(candidates[i]), i))
    chosen = [candidates[i] for i in order[:max_terms]]
    return ";".join(chosen)


def _process_rows(
    reader: csv.DictReader,
    writer: csv.DictWriter,
    *,
    max_terms: int,
    max_fragment_len: int,
    include_ngrams: bool,
    max_rows: int | None,
) -> int:
    if reader.fieldnames is None:
        raise ValueError("CSV has no header row.")
    missing = [h for h in REQUIRED_HEADERS if h not in reader.fieldnames]
    if missing:
        raise ValueError(f"CSV missing headers: {missing}")

    n = 0
    for row in reader:
        desc = row.get("description", "") or ""
        row["searchTerms"] = _terms_for_row(
            desc,
            max_terms=max_terms,
            max_fragment_len=max_fragment_len,
            include_ngrams=include_ngrams,
        )
        writer.writerow({h: row.get(h, "") for h in REQUIRED_HEADERS})
        n += 1
        if max_rows is not None and n >= max_rows:
            break
    return n


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Output CSV (default: {DEFAULT_OUTPUT} unless --in-place)",
    )
    p.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite --input (writes via a temporary file in the same directory)",
    )
    p.add_argument("--max-terms", type=int, default=15, help="Max semicolon-separated search terms per row")
    p.add_argument(
        "--max-fragment-len",
        type=int,
        default=72,
        help="Trim individual search term fragments to this many characters",
    )
    p.add_argument(
        "--ngrams",
        action="store_true",
        help="Add unigrams/bigrams from the first clause (first ~8 words)",
    )
    p.add_argument("--max-rows", type=int, default=None, help="Stop after N data rows (for quick tests)")
    args = p.parse_args()

    in_path: Path = args.input
    if not in_path.is_file():
        raise SystemExit(f"Input not found: {in_path}")

    if args.in_place:
        out_path = in_path
        fd, tmp_name = tempfile.mkstemp(
            suffix=".csv",
            prefix=".enrich-",
            dir=in_path.parent,
            text=True,
        )
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            with in_path.open(encoding="utf-8", newline="") as fin, tmp_path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as tmp:
                reader = csv.DictReader(fin)
                writer = csv.DictWriter(tmp, fieldnames=list(REQUIRED_HEADERS), extrasaction="ignore")
                writer.writeheader()
                count = _process_rows(
                    reader,
                    writer,
                    max_terms=args.max_terms,
                    max_fragment_len=args.max_fragment_len,
                    include_ngrams=args.ngrams,
                    max_rows=args.max_rows,
                )
            shutil.move(str(tmp_path), str(out_path))
        except BaseException:
            tmp_path.unlink(missing_ok=True)
            raise
        print(f"Wrote {count} rows in-place to {out_path}")
        return

    out_path = args.output or DEFAULT_OUTPUT
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with in_path.open(encoding="utf-8", newline="") as fin, out_path.open("w", encoding="utf-8", newline="") as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=list(REQUIRED_HEADERS), extrasaction="ignore")
        writer.writeheader()
        count = _process_rows(
            reader,
            writer,
            max_terms=args.max_terms,
            max_fragment_len=args.max_fragment_len,
            include_ngrams=args.ngrams,
            max_rows=args.max_rows,
        )
    print(f"Wrote {count} rows to {out_path}")


if __name__ == "__main__":
    main()
