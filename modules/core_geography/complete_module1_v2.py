"""Robust completion runner for JLA Module 1.

This wrapper keeps the conservative MDDS and Census↔LGD logic from
``complete_module1.py`` but replaces the DCHB village-amenities parser with a
source-structure-independent parser.  Village-code detection is validated
against the already-verified Census 2011 Jharkhand village backbone, so a
column is accepted because its values are known Census village codes rather
than because a guessed header happens to contain the word 'code'.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from complete_module1 import (
    RAW,
    OUT,
    REPORT,
    _source_meta,
    build_mdds_crosswalk,
    build_census_lgd_temporal_crosswalk,
    norm,
)


def _code6(value: object) -> str:
    s = "" if value is None else str(value).strip()
    m = re.fullmatch(r"(\d{6})(?:\.0+)?", s)
    return m.group(1) if m else ""


def _composite_headers(raw: pd.DataFrame, first_data_row: int) -> list[str]:
    """Build readable, unique headers from the rows immediately above data."""
    start = max(0, first_data_row - 6)
    header_rows = raw.iloc[start:first_data_row]
    names: list[str] = []
    seen: dict[str, int] = {}
    for col in range(raw.shape[1]):
        parts: list[str] = []
        for value in header_rows.iloc[:, col].tolist():
            text = norm(value)
            if text and text not in parts and text not in {"nan", "none"}:
                parts.append(text)
        base = "__".join(parts[-3:]) if parts else f"source_col_{col + 1}"
        count = seen.get(base, 0)
        seen[base] = count + 1
        names.append(base if count == 0 else f"{base}_{count + 1}")
    return names


def build_dchb_amenities_robust() -> tuple[pd.DataFrame, dict]:
    candidates = sorted(RAW.glob("*DCHB*Village*.xlsx")) + sorted(RAW.glob("DH_2011_DCHB*.xlsx"))
    if not candidates:
        raise RuntimeError("Authoritative DCHB village-amenities workbook is missing from the raw sync directory")
    path = max(candidates, key=lambda p: p.stat().st_size)

    census_path = OUT / "census_places_2011.csv"
    census = pd.read_csv(census_path, dtype=str, keep_default_na=False)
    census_codes = set(
        census.loc[census["place_type"] == "village", "village_code"].astype(str).str.zfill(6)
    )
    if len(census_codes) < 30_000:
        raise RuntimeError(f"Verified Census village backbone unexpectedly small: {len(census_codes)}")

    book = pd.ExcelFile(path, engine="openpyxl")
    pieces: list[pd.DataFrame] = []
    diagnostics: list[dict] = []

    for sheet in book.sheet_names:
        raw = pd.read_excel(path, sheet_name=sheet, header=None, dtype=str, engine="openpyxl").fillna("")
        if raw.empty:
            continue

        # Score every column by exact membership in the verified Census village
        # code set.  This avoids trusting ambiguous or multi-row spreadsheet
        # headers and prevents unrelated six-digit values from being published.
        best_col = None
        best_count = 0
        best_codes: pd.Series | None = None
        for col in raw.columns:
            codes = raw[col].map(_code6)
            count = int(codes.isin(census_codes).sum())
            if count > best_count:
                best_col, best_count, best_codes = col, count, codes

        diagnostics.append({"sheet": str(sheet), "matched_census_codes": best_count})
        if best_col is None or best_codes is None or best_count < 10:
            continue

        valid_mask = best_codes.isin(census_codes)
        valid_rows = raw.index[valid_mask]
        first_data_row = int(valid_rows.min())
        headers = _composite_headers(raw, first_data_row)

        data = raw.loc[valid_mask].copy()
        data.columns = headers
        code_col_name = headers[int(best_col)] if isinstance(best_col, int) else headers[list(raw.columns).index(best_col)]
        data["census_village_code_2011"] = best_codes.loc[valid_mask].values
        data["source_sheet"] = str(sheet)
        data["source_code_column"] = code_col_name
        pieces.append(data)

    if not pieces:
        raise RuntimeError(f"No DCHB sheet contained verified Jharkhand Census village codes. Diagnostics: {diagnostics[:20]}")

    work = pd.concat(pieces, ignore_index=True, sort=False).fillna("")
    work = work.drop_duplicates(subset=["census_village_code_2011"], keep="first").copy()

    # Attach the canonical village name from the already-verified Census
    # backbone rather than guessing which DCHB text column contains the name.
    names = census.loc[census["place_type"] == "village", ["village_code", "village_name"]].copy()
    names["village_code"] = names["village_code"].astype(str).str.zfill(6)
    name_map = dict(zip(names["village_code"], names["village_name"]))
    work["village_name"] = work["census_village_code_2011"].map(name_map).fillna("")
    work["place_id"] = "JH-VILL-" + work["census_village_code_2011"]
    work["reference_year"] = "2011"
    work["source_id"] = "CENSUS_DCHB_JH_2011"
    work["observation_type"] = "observed"
    work["quality_class"] = "A"
    meta = _source_meta("village_amenities")
    work["source_sha256"] = str(meta.get("sha256", ""))
    work["source_file"] = path.name

    if len(work) < 30_000:
        raise RuntimeError(
            f"DCHB amenities parsing produced only {len(work)} unique verified village rows. "
            f"Sheet diagnostics: {diagnostics}"
        )

    metadata_cols = {
        "census_village_code_2011", "village_name", "place_id", "reference_year",
        "source_id", "observation_type", "quality_class", "source_sha256",
        "source_file", "source_sheet", "source_code_column",
    }
    source_cols = [c for c in work.columns if c not in metadata_cols]
    nonempty = sum((work[c].astype(str).str.strip() != "").any() for c in source_cols)
    if nonempty < 8:
        raise RuntimeError(f"DCHB amenities parsing retained only {nonempty} populated source fields")

    return work, {
        "rows": int(len(work)),
        "source_fields_populated": int(nonempty),
        "file": path.name,
        "sheet_diagnostics": diagnostics,
        "code_validation": "exact_membership_in_verified_census_2011_village_backbone",
    }


def main() -> None:
    amenities, amenities_counts = build_dchb_amenities_robust()
    amenities.to_csv(OUT / "village_amenities_2011.csv", index=False, encoding="utf-8")

    mdds, mdds_counts = build_mdds_crosswalk()
    mdds.to_csv(OUT / "census_mdds_crosswalk_2001_2011.csv", index=False, encoding="utf-8")

    temporal, temporal_counts = build_census_lgd_temporal_crosswalk()
    temporal.to_csv(OUT / "census_lgd_temporal_crosswalk.csv", index=False, encoding="utf-8")

    report = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {}
    report.setdefault("counts", {})["dchb_village_amenities"] = amenities_counts
    report["counts"]["mdds_2001_2011_crosswalk"] = mdds_counts
    report["counts"]["census_lgd_temporal_crosswalk"] = temporal_counts
    report["module1_completion_layers"] = {
        "dchb_village_amenities": "validated",
        "mdds_2001_2011_crosswalk": "validated",
        "census_lgd_temporal_crosswalk": "validated_with_unmatched_explicit",
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report["module1_completion_layers"], indent=2))
    print(json.dumps({"amenities": amenities_counts, "mdds": mdds_counts, "temporal": temporal_counts}, indent=2))


if __name__ == "__main__":
    main()
