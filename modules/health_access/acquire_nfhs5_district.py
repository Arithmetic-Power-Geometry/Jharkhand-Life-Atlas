"""Acquire and inspect the official NFHS-5 district factsheet workbook.

This script is deliberately fail-closed. It downloads the exact authoritative
OGD workbook, records immutable provenance, discovers the observed workbook
schema, and extracts only rows explicitly labelled Jharkhand. It does not
allocate district estimates to villages/facilities/persons and it preserves
blank/suppressed source cells as missing values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

SOURCE_ID = "OGD_NFHS5_DISTRICT_FACTSHEETS_2019_2021"
SOURCE_URL = "https://data.gov.in/files/ogdpv2dms/s3fs-public/datafile/NFHS_5_India_Districts_Factsheet_Data.xls"
RESOURCE_PAGE = "https://www.data.gov.in/resource/india-districts-factsheets-national-family-health-survey-nfhs-5-2019-2021-provisional"
SOURCE_AUTHORITY = "Ministry of Health and Family Welfare / International Institute for Population Sciences"
REFERENCE_PERIOD = "2019-2021"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"


def _norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().casefold()).strip("_")


def _is_html(data: bytes) -> bool:
    prefix = data[:512].lstrip().lower()
    return prefix.startswith(b"<!doctype html") or prefix.startswith(b"<html")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _find_header_row(raw: pd.DataFrame) -> tuple[int, str, str] | None:
    """Find a row that explicitly contains state and district labels."""
    for idx in range(min(40, len(raw))):
        labels = [_norm(v) for v in raw.iloc[idx].tolist()]
        state_candidates = [x for x in labels if x == "state" or x == "state_ut" or "state_name" in x]
        district_candidates = [x for x in labels if x == "district" or "district_name" in x]
        if state_candidates and district_candidates:
            return idx, state_candidates[0], district_candidates[0]
    return None


def _pick_column(columns: list[str], *, role: str) -> str:
    normalized = {_norm(c): c for c in columns}
    preferred = {
        "state": ["state", "state_ut", "state_name", "state_ut_name"],
        "district": ["district", "district_name"],
    }[role]
    for key in preferred:
        if key in normalized:
            return normalized[key]
    matches = [c for c in columns if role in _norm(c) and "code" not in _norm(c)]
    if len(matches) == 1:
        return matches[0]
    raise RuntimeError(f"Could not uniquely identify {role} column from observed columns: {columns[:30]}")


def _schema_record(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for col in frame.columns:
        series = frame[col]
        nonmissing = int(series.notna().sum())
        records.append({
            "column": str(col),
            "normalized_column": _norm(col),
            "pandas_dtype": str(series.dtype),
            "nonmissing_cells": nonmissing,
            "missing_cells": int(len(series) - nonmissing),
        })
    return records


def _download_official(url: str) -> tuple[bytes, str, list[dict[str, Any]]]:
    """Download using an OGD page session and auditable fallback attempts.

    data.gov.in can reject direct hot-linked file requests from cloud runners.
    We first establish a same-site session on the authoritative resource page,
    then retry the exact official asset with browser-like headers. No mirror or
    third-party copy is accepted as authoritative payload evidence.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
    })
    attempts: list[dict[str, Any]] = []
    try:
        landing = session.get(RESOURCE_PAGE, timeout=90, allow_redirects=True)
        attempts.append({"stage": "resource_page_session", "status_code": landing.status_code, "final_url": landing.url})
    except requests.RequestException as exc:
        attempts.append({"stage": "resource_page_session", "error": f"{type(exc).__name__}: {exc}"})

    candidates = [url]
    if url.startswith("https://data.gov.in/"):
        candidates.append(url.replace("https://data.gov.in/", "https://www.data.gov.in/", 1))
    for candidate in candidates:
        headers = {
            "Referer": RESOURCE_PAGE,
            "Accept": "application/vnd.ms-excel,application/octet-stream,*/*;q=0.8",
        }
        try:
            response = session.get(candidate, headers=headers, timeout=180, allow_redirects=True)
            attempts.append({
                "stage": "official_asset",
                "requested_url": candidate,
                "status_code": response.status_code,
                "final_url": response.url,
                "bytes_received": len(response.content),
                "content_type": response.headers.get("Content-Type", ""),
            })
            if response.status_code == 200 and response.content and not _is_html(response.content):
                return response.content, response.url, attempts
        except requests.RequestException as exc:
            attempts.append({"stage": "official_asset", "requested_url": candidate, "error": f"{type(exc).__name__}: {exc}"})

    raise RuntimeError("Official NFHS-5 payload acquisition failed without using a mirror; attempts=" + json.dumps(attempts, ensure_ascii=False))


def acquire(output_dir: Path, *, url: str = SOURCE_URL) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    data, final_url, acquisition_attempts = _download_official(url)
    if len(data) < 50_000:
        raise RuntimeError(f"NFHS-5 workbook payload is implausibly small: {len(data)} bytes")

    raw_path = output_dir / "NFHS_5_India_Districts_Factsheet_Data.xls"
    raw_path.write_bytes(data)
    digest = _sha256(data)

    book = pd.ExcelFile(raw_path, engine="xlrd")
    if not book.sheet_names:
        raise RuntimeError("NFHS-5 workbook contains no sheets")

    extracted: list[pd.DataFrame] = []
    sheet_reports: list[dict[str, Any]] = []
    for sheet in book.sheet_names:
        raw = pd.read_excel(raw_path, sheet_name=sheet, header=None, dtype=object, engine="xlrd")
        header = _find_header_row(raw)
        if header is None:
            sheet_reports.append({"sheet": str(sheet), "status": "no_explicit_state_district_header"})
            continue
        header_row, _, _ = header
        frame = pd.read_excel(raw_path, sheet_name=sheet, header=header_row, dtype=object, engine="xlrd")
        frame = frame.dropna(how="all").copy()
        frame.columns = [str(c).strip() for c in frame.columns]
        state_col = _pick_column(list(frame.columns), role="state")
        district_col = _pick_column(list(frame.columns), role="district")
        state_norm = frame[state_col].map(_norm)
        jh = frame.loc[state_norm == "jharkhand"].copy()
        sheet_reports.append({
            "sheet": str(sheet),
            "status": "parsed",
            "header_row_zero_based": int(header_row),
            "state_column": state_col,
            "district_column": district_col,
            "rows_total": int(len(frame)),
            "jharkhand_rows": int(len(jh)),
            "columns": _schema_record(frame),
        })
        if jh.empty:
            continue
        if jh[district_col].isna().any() or (jh[district_col].astype(str).str.strip() == "").any():
            raise RuntimeError(f"Jharkhand rows in sheet {sheet!r} contain missing district labels")
        jh.insert(0, "jla_source_id", SOURCE_ID)
        jh.insert(1, "jla_reference_period", REFERENCE_PERIOD)
        jh.insert(2, "jla_source_sheet", str(sheet))
        jh.insert(3, "jla_source_sha256", digest)
        jh.insert(4, "jla_observation_type", "observed_district_fact_sheet_estimate")
        jh.insert(5, "jla_geography_scope", "source_district_2019_2021_not_crosswalked_to_current_lgd")
        extracted.append(jh)

    if not extracted:
        raise RuntimeError("No rows explicitly labelled Jharkhand were found in any parsed NFHS-5 sheet")

    curated = pd.concat(extracted, ignore_index=True, sort=False)
    if len(curated) < 20:
        raise RuntimeError(f"NFHS-5 Jharkhand district extraction is implausibly small: {len(curated)} rows")

    curated_path = output_dir / "nfhs5_jharkhand_district_factsheet_candidate.csv"
    curated.to_csv(curated_path, index=False, encoding="utf-8", na_rep="")

    schema_path = output_dir / "nfhs5_observed_schema.json"
    schema_path.write_text(json.dumps({"sheets": sheet_reports}, indent=2, ensure_ascii=False), encoding="utf-8")

    receipt = {
        "contract": "JLA_SOURCE_SNAPSHOT_V1",
        "source_id": SOURCE_ID,
        "authority": SOURCE_AUTHORITY,
        "exact_source_url": url,
        "final_official_payload_url": final_url,
        "retrieved_at_utc": retrieved_at,
        "retrieval_method": "same_site_resource_session_then_https_get_official_data_gov_in_asset",
        "acquisition_attempts": acquisition_attempts,
        "raw_filename": raw_path.name,
        "byte_count": len(data),
        "sha256": digest,
        "reference_period": REFERENCE_PERIOD,
        "rights": {
            "status": "reviewed_ogdl_platform_with_attribution",
            "licence": "Government Open Data License - India",
            "attribution_required": True,
        },
        "observed_schema_file": schema_path.name,
        "jharkhand_candidate_file": curated_path.name,
        "jharkhand_candidate_rows": int(len(curated)),
        "geography": {
            "source_granularity": "district",
            "linkage_status": "source_district_labels_preserved_not_crosswalked_to_current_lgd",
            "direct_name_equivalence_to_other_vintages_allowed": False,
        },
        "null_semantics": "source blanks/suppression/annotation retained; no missing-to-zero conversion",
        "publication_allowed": False,
        "publication_blocker": "candidate requires schema/indicator semantics review, survey-quality annotation review, district-vintage linkage validation and tests before JLA publication",
    }
    receipt_path = output_dir / "nfhs5_acquisition_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire official NFHS-5 district factsheet payload")
    parser.add_argument("--output-dir", type=Path, default=Path("build/health_nfhs5"))
    parser.add_argument("--url", default=SOURCE_URL)
    args = parser.parse_args()
    receipt = acquire(args.output_dir, url=args.url)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
