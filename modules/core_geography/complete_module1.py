"""Complete the remaining authoritative layers for JLA Module 1.

Runs immediately after ``sync_fast_runner.py`` in the same GitHub Actions job, so
its inputs are the freshly downloaded official Census files plus the curated
Census/LGD tables.  The implementation is deliberately conservative:

* source columns are preserved rather than re-interpreted silently;
* Census and current LGD remain separate temporal views;
* crosswalks use official codes when available and otherwise record an explicit
  unmatched status;
* missing values are never converted to zero;
* structural/coverage checks fail the workflow instead of publishing dubious
  outputs.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "core_geography"
OUT = ROOT / "data" / "curated" / "core_geography"
REPORT = ROOT / "modules" / "core_geography" / "sync_report.json"


def norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def digits(value: object) -> str:
    m = re.search(r"\d+", "" if value is None else str(value))
    return m.group(0) if m else ""


def _dedupe_columns(columns: Iterable[object]) -> list[str]:
    seen: dict[str, int] = {}
    out: list[str] = []
    for raw in columns:
        base = norm(raw) or "unnamed"
        count = seen.get(base, 0)
        seen[base] = count + 1
        out.append(base if count == 0 else f"{base}_{count + 1}")
    return out


def _read_best_table(path: Path, *, header_terms: tuple[str, ...]) -> pd.DataFrame:
    """Find the most plausible data sheet/header without assuming a fixed layout."""
    engine = "xlrd" if path.suffix.lower() == ".xls" else "openpyxl"
    book = pd.ExcelFile(path, engine=engine)
    best: tuple[int, str, int] | None = None
    diagnostics: list[str] = []
    for sheet in book.sheet_names:
        probe = pd.read_excel(path, sheet_name=sheet, header=None, nrows=45,
                              dtype=str, engine=engine).fillna("")
        for idx in range(len(probe)):
            cells = [norm(x) for x in probe.iloc[idx].tolist() if str(x).strip()]
            line = " ".join(cells)
            score = sum(3 for term in header_terms if term in line)
            score += min(len(cells), 20) // 4
            if "village" in line:
                score += 4
            if "code" in line:
                score += 3
            diagnostics.append(f"{sheet}:{idx}:{score}:{line[:180]}")
            if best is None or score > best[0]:
                best = (score, sheet, idx)
    if best is None or best[0] < 8:
        raise RuntimeError(
            f"Could not identify a defensible table/header in {path.name}. "
            f"Best diagnostics: {sorted(diagnostics, reverse=True)[:5]}"
        )
    _, sheet, header = best
    df = pd.read_excel(path, sheet_name=sheet, header=header, dtype=str, engine=engine).fillna("")
    df.columns = _dedupe_columns(df.columns)
    # Drop fully empty rows/columns while preserving source values verbatim.
    df = df.loc[:, [c for c in df.columns if (df[c].astype(str).str.strip() != "").any()]]
    df = df[(df.astype(str).apply(lambda s: s.str.strip()).ne("")).any(axis=1)].copy()
    return df


def _pick(cols: list[str], *, all_terms: tuple[str, ...] = (), any_terms: tuple[str, ...] = (),
          exclude: tuple[str, ...] = ()) -> str | None:
    ranked: list[tuple[int, str]] = []
    for c in cols:
        n = norm(c)
        if any(x in n for x in exclude):
            continue
        if all_terms and not all(x in n for x in all_terms):
            continue
        if any_terms and not any(x in n for x in any_terms):
            continue
        score = sum(4 for x in all_terms if x in n) + sum(1 for x in any_terms if x in n)
        score -= len(n) // 80
        ranked.append((score, c))
    return max(ranked)[1] if ranked else None


def _source_meta(key: str) -> dict:
    if not REPORT.exists():
        return {}
    try:
        return json.loads(REPORT.read_text(encoding="utf-8")).get("sources", {}).get(key, {})
    except Exception:
        return {}


def build_dchb_amenities() -> tuple[pd.DataFrame, dict]:
    candidates = sorted(RAW.glob("*DCHB*Village*.xlsx")) + sorted(RAW.glob("DH_2011_DCHB*.xlsx"))
    if not candidates:
        raise RuntimeError("Authoritative DCHB village-amenities workbook is missing from the raw sync directory")
    path = max(candidates, key=lambda p: p.stat().st_size)
    df = _read_best_table(path, header_terms=("village", "code", "education", "medical"))
    cols = list(df.columns)

    code_col = (
        _pick(cols, all_terms=("village", "code"), exclude=("2001",))
        or _pick(cols, all_terms=("location", "code"))
    )
    name_col = _pick(cols, all_terms=("village", "name")) or _pick(cols, all_terms=("name",), any_terms=("village",))
    if not code_col:
        raise RuntimeError(f"DCHB village-code column not recognised. Columns: {cols[:80]}")

    work = df.copy()
    work["census_village_code_2011"] = work[code_col].map(digits).map(lambda x: x.zfill(6) if x else "")
    work = work[work["census_village_code_2011"].str.match(r"^\d{6}$")].copy()
    work["village_name"] = work[name_col].astype(str).str.strip() if name_col else ""
    work["place_id"] = "JH-VILL-" + work["census_village_code_2011"]
    work["reference_year"] = "2011"
    work["source_id"] = "CENSUS_DCHB_JH_2011"
    work["observation_type"] = "observed"
    work["quality_class"] = "A"
    meta = _source_meta("village_amenities")
    work["source_sha256"] = str(meta.get("sha256", ""))
    work["source_file"] = path.name
    work = work.drop_duplicates(subset=["census_village_code_2011"], keep="first")

    # A statewide village directory should cover the overwhelming majority of
    # Jharkhand Census villages. The threshold is deliberately below 32,624 to
    # accommodate source-specific handling of uninhabited/merged records.
    if len(work) < 30_000:
        raise RuntimeError(f"DCHB amenities parsing produced only {len(work)} unique village rows")
    source_cols = [c for c in cols if c not in {code_col, name_col}]
    nonempty = sum((work[c].astype(str).str.strip() != "").any() for c in source_cols if c in work.columns)
    if nonempty < 8:
        raise RuntimeError(f"DCHB amenities parsing retained only {nonempty} populated source fields")
    return work, {"rows": int(len(work)), "source_fields_populated": int(nonempty), "file": path.name}


def build_mdds_crosswalk() -> tuple[pd.DataFrame, dict]:
    path = RAW / "Rdir_2001_MDDS_20.xls"
    if not path.exists():
        matches = sorted(RAW.glob("*MDDS*20*.xls"))
        if not matches:
            raise RuntimeError("Authoritative Jharkhand MDDS workbook is missing from the raw sync directory")
        path = matches[0]
    df = _read_best_table(path, header_terms=("village", "2001", "2011", "code"))
    cols = list(df.columns)

    code2011 = (
        _pick(cols, all_terms=("2011", "village", "code"))
        or _pick(cols, all_terms=("2011", "code"), any_terms=("village", "location"))
        or _pick(cols, all_terms=("new", "village", "code"))
    )
    code2001 = (
        _pick(cols, all_terms=("2001", "village", "code"))
        or _pick(cols, all_terms=("2001", "code"), any_terms=("village", "location"))
        or _pick(cols, all_terms=("old", "village", "code"))
    )
    name2011 = _pick(cols, all_terms=("2011", "village", "name")) or _pick(cols, all_terms=("village", "name"), exclude=("2001",))
    name2001 = _pick(cols, all_terms=("2001", "village", "name"))
    district = _pick(cols, all_terms=("district", "name"))
    subdistrict = _pick(cols, all_terms=("sub", "district", "name")) or _pick(cols, all_terms=("tehsil", "name"))

    if not code2011 or not code2001:
        raise RuntimeError(
            "MDDS 2001↔2011 village-code columns could not be identified without guessing. "
            f"Columns: {cols[:100]}"
        )

    out = pd.DataFrame({
        "census_village_code_2011": df[code2011].map(digits).map(lambda x: x.zfill(6) if x else ""),
        "census_village_code_2001": df[code2001].map(digits).map(lambda x: x.zfill(6) if x else ""),
        "village_name_2011": df[name2011].astype(str).str.strip() if name2011 else "",
        "village_name_2001": df[name2001].astype(str).str.strip() if name2001 else "",
        "district_name": df[district].astype(str).str.strip() if district else "",
        "subdistrict_name": df[subdistrict].astype(str).str.strip() if subdistrict else "",
    })
    out = out[(out["census_village_code_2011"] != "") | (out["census_village_code_2001"] != "")].copy()
    out["match_status"] = "linked_2001_2011"
    out.loc[(out["census_village_code_2001"] == "") & (out["census_village_code_2011"] != ""), "match_status"] = "no_2001_code_in_source"
    out.loc[(out["census_village_code_2001"] != "") & (out["census_village_code_2011"] == ""), "match_status"] = "no_2011_code_in_source"
    out["reference_year"] = "2001-2011"
    out["source_id"] = "CENSUS_MDDS_JH_2011"
    out["observation_type"] = "observed_crosswalk"
    out["quality_class"] = "A"
    meta = _source_meta("mdds_jh")
    out["source_sha256"] = str(meta.get("sha256", ""))
    out["source_file"] = path.name
    out = out.drop_duplicates().reset_index(drop=True)

    linked = int(((out["census_village_code_2011"] != "") & (out["census_village_code_2001"] != "")).sum())
    if len(out) < 25_000 or linked < 20_000:
        raise RuntimeError(f"MDDS crosswalk coverage implausible: rows={len(out)}, linked={linked}")
    return out, {"rows": int(len(out)), "linked": linked, "file": path.name}


def build_census_lgd_temporal_crosswalk() -> tuple[pd.DataFrame, dict]:
    census_path = OUT / "census_places_2011.csv"
    lgd_path = OUT / "lgd_villages_current.csv"
    census = pd.read_csv(census_path, dtype=str, keep_default_na=False)
    lgd = pd.read_csv(lgd_path, dtype=str, keep_default_na=False)
    census = census[census["place_type"] == "village"].copy()

    lgd.columns = _dedupe_columns(lgd.columns)
    cols = list(lgd.columns)
    lgd_code = _pick(cols, all_terms=("village", "code"), exclude=("census",)) or _pick(cols, all_terms=("villagecode",))
    lgd_name = _pick(cols, all_terms=("village", "name")) or _pick(cols, all_terms=("villagename",))
    census_code = (
        _pick(cols, all_terms=("census", "2011", "code"))
        or _pick(cols, all_terms=("census2011", "code"))
        or _pick(cols, all_terms=("village", "census", "code"), exclude=("2001",))
    )

    base = census[["village_code", "village_name", "district_code", "subdistrict_code", "place_id"]].copy()
    base = base.rename(columns={"village_code": "census_village_code_2011", "village_name": "census_village_name_2011"})
    base["lgd_village_code_current"] = ""
    base["lgd_village_name_current"] = ""
    base["match_method"] = ""
    base["match_status"] = "unmatched_no_official_census2011_code_in_lgd_response"

    matched = 0
    if census_code and lgd_code:
        link = lgd.copy()
        link["_census"] = link[census_code].map(digits).map(lambda x: x.zfill(6) if x else "")
        link["_lgd"] = link[lgd_code].map(digits)
        link = link[(link["_census"] != "") & (link["_lgd"] != "")].copy()
        link = link.drop_duplicates(subset=["_census"], keep=False)
        mapping = link.set_index("_census")
        idx = base["census_village_code_2011"].isin(mapping.index)
        for i in base.index[idx]:
            key = base.at[i, "census_village_code_2011"]
            base.at[i, "lgd_village_code_current"] = str(mapping.at[key, "_lgd"])
            base.at[i, "lgd_village_name_current"] = str(mapping.at[key, lgd_name]) if lgd_name else ""
            base.at[i, "match_method"] = f"official_lgd_field:{census_code}"
            base.at[i, "match_status"] = "linked_by_official_census2011_code"
        matched = int(idx.sum())

    base["census_reference_year"] = "2011"
    base["lgd_reference_period"] = "current"
    base["source_id"] = "CENSUS_LOCATION_DIR_2011+LGD_CURRENT"
    base["observation_type"] = "temporal_crosswalk"
    base["quality_class"] = "A" if matched else "B"
    if len(base) < 30_000:
        raise RuntimeError(f"Census↔LGD crosswalk base unexpectedly small: {len(base)}")
    return base, {"census_villages": int(len(base)), "official_code_links": matched,
                  "lgd_census2011_field": census_code or "not_exposed"}


def main() -> None:
    amenities, amenities_counts = build_dchb_amenities()
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
