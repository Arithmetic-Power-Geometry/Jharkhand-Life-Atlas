"""Robust completion runner for JLA Module 1.

The completion layer deliberately validates ambiguous Census workbooks against
already-verified structure instead of trusting fragile one-row headers.
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
    build_census_lgd_temporal_crosswalk,
    norm,
)


def _code6(value: object) -> str:
    s = "" if value is None else str(value).strip()
    m = re.fullmatch(r"(\d{6})(?:\.0+)?", s)
    return m.group(1) if m else ""


def _digits(value: object) -> str:
    s = "" if value is None else str(value).strip()
    m = re.fullmatch(r"(\d+)(?:\.0+)?", s)
    return m.group(1) if m else ""


def _composite_headers(raw: pd.DataFrame, first_data_row: int) -> list[str]:
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


def _structured_mdds_headers(raw: pd.DataFrame, first_data_row: int) -> list[str]:
    """Reconstruct multi-row MDDS headers, including merged group labels.

    The official workbook uses grouped 2001 and 2011 headings.  We propagate a
    group label only across adjacent blank cells in the same header row, then
    combine it with the column-level labels below it.  This makes selection
    depend on explicit source labels rather than column position.
    """
    start = max(0, first_data_row - 10)
    hdr = raw.iloc[start:first_data_row].copy().fillna("")
    rows: list[list[str]] = []
    for _, row in hdr.iterrows():
        vals = [norm(x) for x in row.tolist()]
        # A row containing both group concepts is a grouped/merged header row.
        joined = " ".join(v for v in vals if v)
        if "2001" in joined and "2011" in joined:
            current = ""
            ff: list[str] = []
            for v in vals:
                if v:
                    current = v
                ff.append(current)
            vals = ff
        rows.append(vals)

    names: list[str] = []
    seen: dict[str, int] = {}
    for col in range(raw.shape[1]):
        parts: list[str] = []
        for vals in rows:
            if col >= len(vals):
                continue
            v = vals[col]
            if v and v not in {"nan", "none"} and v not in parts:
                parts.append(v)
        base = "__".join(parts[-4:]) if parts else f"source_col_{col + 1}"
        count = seen.get(base, 0)
        seen[base] = count + 1
        names.append(base if count == 0 else f"{base}_{count + 1}")
    return names


def build_dchb_amenities_robust() -> tuple[pd.DataFrame, dict]:
    candidates = sorted(RAW.glob("*DCHB*Village*.xlsx")) + sorted(RAW.glob("DH_2011_DCHB*.xlsx"))
    if not candidates:
        raise RuntimeError("Authoritative DCHB village-amenities workbook is missing from the raw sync directory")
    path = max(candidates, key=lambda p: p.stat().st_size)

    census = pd.read_csv(OUT / "census_places_2011.csv", dtype=str, keep_default_na=False)
    census_codes = set(census.loc[census["place_type"] == "village", "village_code"].astype(str).str.zfill(6))
    if len(census_codes) < 30_000:
        raise RuntimeError(f"Verified Census village backbone unexpectedly small: {len(census_codes)}")

    book = pd.ExcelFile(path, engine="openpyxl")
    pieces: list[pd.DataFrame] = []
    diagnostics: list[dict] = []
    for sheet in book.sheet_names:
        raw = pd.read_excel(path, sheet_name=sheet, header=None, dtype=str, engine="openpyxl").fillna("")
        if raw.empty:
            continue
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
        first_data_row = int(raw.index[valid_mask].min())
        headers = _composite_headers(raw, first_data_row)
        data = raw.loc[valid_mask].copy()
        data.columns = headers
        data["census_village_code_2011"] = best_codes.loc[valid_mask].values
        data["source_sheet"] = str(sheet)
        data["source_code_column"] = headers[int(best_col)]
        pieces.append(data)

    if not pieces:
        raise RuntimeError(f"No DCHB sheet contained verified Jharkhand Census village codes. Diagnostics: {diagnostics[:20]}")
    work = pd.concat(pieces, ignore_index=True, sort=False).fillna("")
    work = work.drop_duplicates(subset=["census_village_code_2011"], keep="first").copy()

    names = census.loc[census["place_type"] == "village", ["village_code", "village_name"]].copy()
    names["village_code"] = names["village_code"].astype(str).str.zfill(6)
    work["village_name"] = work["census_village_code_2011"].map(dict(zip(names["village_code"], names["village_name"]))).fillna("")
    work["place_id"] = "JH-VILL-" + work["census_village_code_2011"]
    work["reference_year"] = "2011"
    work["source_id"] = "CENSUS_DCHB_JH_2011"
    work["observation_type"] = "observed"
    work["quality_class"] = "A"
    meta = _source_meta("village_amenities")
    work["source_sha256"] = str(meta.get("sha256", ""))
    work["source_file"] = path.name

    if len(work) < 30_000:
        raise RuntimeError(f"DCHB amenities parsing produced only {len(work)} unique verified village rows. Sheet diagnostics: {diagnostics}")
    metadata_cols = {"census_village_code_2011", "village_name", "place_id", "reference_year", "source_id", "observation_type", "quality_class", "source_sha256", "source_file", "source_sheet", "source_code_column"}
    source_cols = [c for c in work.columns if c not in metadata_cols]
    nonempty = sum((work[c].astype(str).str.strip() != "").any() for c in source_cols)
    if nonempty < 8:
        raise RuntimeError(f"DCHB amenities parsing retained only {nonempty} populated source fields")
    return work, {"rows": int(len(work)), "source_fields_populated": int(nonempty), "file": path.name, "sheet_diagnostics": diagnostics, "code_validation": "exact_membership_in_verified_census_2011_village_backbone"}


def build_mdds_crosswalk_robust() -> tuple[pd.DataFrame, dict]:
    path = RAW / "Rdir_2001_MDDS_20.xls"
    if not path.exists():
        matches = sorted(RAW.glob("*MDDS*20*.xls"))
        if not matches:
            raise RuntimeError("Authoritative Jharkhand MDDS workbook is missing from the raw sync directory")
        path = matches[0]

    census = pd.read_csv(OUT / "census_places_2011.csv", dtype=str, keep_default_na=False)
    census_codes = set(census.loc[census["place_type"] == "village", "village_code"].astype(str).str.zfill(6))
    book = pd.ExcelFile(path, engine="xlrd")
    pieces: list[pd.DataFrame] = []
    diagnostics: list[dict] = []

    for sheet in book.sheet_names:
        raw = pd.read_excel(path, sheet_name=sheet, header=None, dtype=str, engine="xlrd").fillna("")
        if raw.empty:
            continue
        # Identify the 2011 village-code column by exact membership in the
        # already-verified Census 2011 Jharkhand village backbone.
        best_2011 = None
        best_count = 0
        best_codes: pd.Series | None = None
        for col in raw.columns:
            codes = raw[col].map(_code6)
            count = int(codes.isin(census_codes).sum())
            if count > best_count:
                best_2011, best_count, best_codes = col, count, codes
        diagnostics.append({"sheet": str(sheet), "verified_2011_codes": best_count})
        if best_2011 is None or best_codes is None or best_count < 100:
            continue

        valid_2011 = best_codes.isin(census_codes)
        first_data_row = int(raw.index[valid_2011].min())
        headers = _structured_mdds_headers(raw, first_data_row)
        header_norm = [norm(h) for h in headers]

        # Require the leaf/column-level source label itself to identify a code
        # field.  The merged parent heading contains the word "codes" for both
        # the code and name columns, so matching the full composite header would
        # incorrectly classify the village-name column as a second code column.
        candidates_2001: list[int] = []
        for i, h in enumerate(header_norm):
            parts = h.split("__")
            group = parts[0] if parts else h
            leaf = parts[-1] if parts else h
            explicit_leaf_code = (
                "plcn" in leaf
                or "village_code" in leaf
                or "location_code" in leaf
            )
            if "2001" in group and "name" not in leaf and explicit_leaf_code:
                candidates_2001.append(i)

        if len(candidates_2001) != 1:
            raise RuntimeError(
                "MDDS 2001 village-code column is not uniquely identified by explicit source headers. "
                f"Sheet={sheet}; candidate_headers={[headers[i] for i in candidates_2001]}; headers={headers[:20]}"
            )
        col2001 = raw.columns[candidates_2001[0]]
        codes2001 = raw[col2001].map(_digits).map(lambda x: x.zfill(6) if x else "")

        # Keep rows carrying an authoritative 2011 village code; retain blank
        # 2001 codes explicitly rather than manufacturing a historical match.
        data = raw.loc[valid_2011].copy()
        out = pd.DataFrame({
            "census_village_code_2011": best_codes.loc[valid_2011].values,
            "census_village_code_2001": codes2001.loc[valid_2011].values,
        })
        # Preserve every source cell with reconstructed headers for auditability.
        data.columns = headers
        for c in data.columns:
            out[f"source__{c}"] = data[c].astype(str).values
        out["source_sheet"] = str(sheet)
        out["source_2011_code_column"] = headers[int(best_2011)]
        out["source_2001_code_column"] = headers[candidates_2001[0]]
        pieces.append(out)

    if not pieces:
        raise RuntimeError(f"No MDDS sheet contained a defensible verified 2011 village-code column. Diagnostics: {diagnostics}")

    out = pd.concat(pieces, ignore_index=True, sort=False).fillna("")
    out = out.drop_duplicates(subset=["census_village_code_2011", "census_village_code_2001"], keep="first")
    name_map = dict(zip(
        census.loc[census["place_type"] == "village", "village_code"].astype(str).str.zfill(6),
        census.loc[census["place_type"] == "village", "village_name"].astype(str),
    ))
    out["village_name_2011"] = out["census_village_code_2011"].map(name_map).fillna("")
    out["match_status"] = "linked_2001_2011"
    out.loc[out["census_village_code_2001"] == "", "match_status"] = "no_2001_code_in_source"
    out["reference_year"] = "2001-2011"
    out["source_id"] = "CENSUS_MDDS_JH_2011"
    out["observation_type"] = "observed_crosswalk"
    out["quality_class"] = "A"
    meta = _source_meta("mdds_jh")
    out["source_sha256"] = str(meta.get("sha256", ""))
    out["source_file"] = path.name

    linked = int((out["census_village_code_2001"] != "").sum())
    verified_2011 = int(out["census_village_code_2011"].isin(census_codes).sum())
    if len(out) < 25_000 or linked < 20_000 or verified_2011 != len(out):
        raise RuntimeError(f"MDDS crosswalk coverage implausible: rows={len(out)}, linked={linked}, verified_2011={verified_2011}")
    return out, {"rows": int(len(out)), "linked": linked, "verified_2011": verified_2011, "file": path.name, "sheet_diagnostics": diagnostics, "validation": "2011 exact Census membership + explicit reconstructed 2001 source header"}


def main() -> None:
    amenities, amenities_counts = build_dchb_amenities_robust()
    amenities.to_csv(OUT / "village_amenities_2011.csv", index=False, encoding="utf-8")

    mdds, mdds_counts = build_mdds_crosswalk_robust()
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
