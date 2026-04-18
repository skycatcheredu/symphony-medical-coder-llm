#!/usr/bin/env python3
"""Download CMS ICD-10-CM / ICD-10-PCS code files and build ontology CSV.

Defaults target the April 1, 2026 CMS bundles (encounters Apr 1 – Sep 30, 2026).
Sources: https://www.cms.gov/medicare/coding-billing/icd-10-codes/

Usage:
  uv run python scripts/build_ontology_cms.py
  uv run python scripts/build_ontology_cms.py --output data/ontology/codes.csv
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import io
import zipfile
from pathlib import Path

import httpx

DEFAULT_CM_ZIP = (
    "https://www.cms.gov/files/zip/april-1-2026-code-descriptions-tabular-order.zip"
)
DEFAULT_PCS_ZIP = "https://www.cms.gov/files/zip/april-1-2026-icd-10-pcs-codes-file.zip"
DEFAULT_OUTPUT = Path("data/ontology/codes.csv")
CM_CODE_FIELD_WIDTH = 8
PCS_CODE_LEN = 7

HEADERS = ("code", "description", "codingSystem", "category", "searchTerms")


def _find_zip_member(names: list[str], glob: str, *, exclude: tuple[str, ...] = ()) -> str:
    for name in names:
        base = Path(name).name
        if not fnmatch.fnmatch(base.lower(), glob.lower()):
            continue
        if any(x in base.lower() for x in exclude):
            continue
        return name
    raise FileNotFoundError(
        f"No member matching {glob!r} (exclude {exclude}) in zip; got: {names[:20]}...",
    )


def _download(url: str, cache_path: Path | None) -> bytes:
    if cache_path and cache_path.is_file():
        return cache_path.read_bytes()
    with httpx.Client(follow_redirects=True, timeout=120.0) as client:
        r = client.get(url)
        r.raise_for_status()
        data = r.content
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(data)
    return data


def _format_icd10_cm_code(raw: str) -> str:
    s = raw.strip().upper()
    if len(s) <= 3:
        return s
    return f"{s[:3]}.{s[3:]}"


def _iter_icd10_cm_rows(zip_bytes: bytes) -> list[tuple[str, str]]:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        member = _find_zip_member(
            zf.namelist(),
            "icd10cm_codes_*.txt",
            exclude=("addenda",),
        )
        text = zf.read(member).decode("utf-8", errors="replace")
    rows: list[tuple[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if len(line) < CM_CODE_FIELD_WIDTH + 2:
            continue
        code_raw = line[:CM_CODE_FIELD_WIDTH].strip()
        desc = line[CM_CODE_FIELD_WIDTH:].strip()
        if not code_raw or not desc:
            continue
        rows.append((_format_icd10_cm_code(code_raw), desc))
    return rows


def _iter_icd10_pcs_rows(zip_bytes: bytes) -> list[tuple[str, str]]:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        member = _find_zip_member(zf.namelist(), "icd10pcs_codes_*.txt", exclude=("addenda",))
        text = zf.read(member).decode("utf-8", errors="replace")
    rows: list[tuple[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.replace("\r", "").strip()
        if not line:
            continue
        if len(line) < PCS_CODE_LEN + 2:
            continue
        code = line[:PCS_CODE_LEN].strip().upper()
        desc = line[PCS_CODE_LEN:].strip()
        if len(code) != PCS_CODE_LEN or not desc:
            continue
        rows.append((code, desc))
    return rows


def build_csv(cm_zip: bytes, pcs_zip: bytes, output: Path) -> tuple[int, int]:
    cm_rows = _iter_icd10_cm_rows(cm_zip)
    pcs_rows = _iter_icd10_pcs_rows(pcs_zip)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADERS)
        for code, desc in cm_rows:
            w.writerow([code, desc, "ICD-10-CM", "diagnosis", ""])
        for code, desc in pcs_rows:
            w.writerow([code, desc, "ICD-10-PCS", "procedure", ""])
    return len(cm_rows), len(pcs_rows)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="CSV path to write")
    p.add_argument("--cm-url", default=DEFAULT_CM_ZIP, help="ZIP URL for ICD-10-CM tabular descriptions")
    p.add_argument("--pcs-url", default=DEFAULT_PCS_ZIP, help="ZIP URL for ICD-10-PCS codes file")
    p.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(".cache/cms-ontology"),
        help="Directory to cache downloaded ZIPs (reused on rerun).",
    )
    p.add_argument("--no-cache", action="store_true", help="Do not read or write ZIP cache on disk.")
    args = p.parse_args()
    cache_dir: Path | None = None if args.no_cache else args.cache_dir

    cm_cache = (cache_dir / "icd10cm.zip") if cache_dir else None
    pcs_cache = (cache_dir / "icd10pcs.zip") if cache_dir else None

    print("Downloading ICD-10-CM …", args.cm_url)
    cm_bytes = _download(args.cm_url, cm_cache)
    print("Downloading ICD-10-PCS …", args.pcs_url)
    pcs_bytes = _download(args.pcs_url, pcs_cache)

    n_cm, n_pcs = build_csv(cm_bytes, pcs_bytes, args.output)
    print(f"Wrote {args.output} ({n_cm} CM + {n_pcs} PCS = {n_cm + n_pcs} rows).")


if __name__ == "__main__":
    main()
