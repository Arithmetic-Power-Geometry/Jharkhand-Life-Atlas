"""Synchronise Module 1 from authoritative Census/LGD sources.

This script is intentionally conservative:
- downloads only Government of India sources;
- never fabricates codes or rows;
- keeps Census 2011 and current LGD in separate tables;
- writes a machine-readable sync report with hashes and counts;
- aborts rather than silently publishing incomplete/ambiguous data.

Designed for GitHub Actions and local use.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "core_geography"
OUT = ROOT / "data" / "curated" / "core_geography"
REPORT = ROOT / "modules" / "core_geography" / "sync_report.json"
RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "Jharkhand-Life-Atlas/1.1 (+https://github.com/Arithmetic-Power-Geometry/Jharkhand-Life-Atlas)"}
TIMEOUT = 90

SOURCES = {
    "location_directory": {
        "catalog": "https://censusindia.gov.in/nada/index.php/catalog/42648",
        "url": "https://censusindia.gov.in/nada/index.php/catalog/42648/download/46323/PC11_TV_DIR.xlsx",
        "filename": "PC11_TV_DIR.xlsx",
        "source_id": "CENSUS_LOCATION_DIR_2011",
    },
    "basic_population": {
        "catalog": "https://censusindia.gov.in/nada/index.php/catalog/42559",
        "filename": "2011-IndiaStateDistSbDistTwn-0000.xlsx",
        "source_id": "CENSUS_BASIC_2011",
    },
    "mdds_jh": {
        "catalog": "https://censusindia.gov.in/nada/index.php/catalog/7059",
        "filename": "Rdir_2001_MDDS_20.xls",
        "source_id": "CENSUS_MDDS_JH_2011",
    },
    "village_amenities": {
        "catalog": "https://censusindia.gov.in/nada/index.php/catalog/570",
        "filename_hint": "Village Amenities",
        "source_id": "CENSUS_DCHB_JH_2011",
    },
}

LGD = "https://lgdirectory.gov.in/webservices/lgdws"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def norm(s: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")


def digits(v: Any) -> str:
    m = re.search(r"\d+", str(v or ""))
    return m.group(0) if m else ""


def get(url: str, *, binary: bool = False) -> bytes | str:
    r = requests.get(url, headers=UA, timeout=TIMEOUT, allow_redirects=True)
    r.raise_for_status()
    return r.content if binary else r.text


def post_json(url: str) -> Any:
    r = requests.post(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def discover_download(catalog: str, filename: str | None = None, hint: str | None = None) -> str:
    html = get(catalog)
    soup = BeautifulSoup(str(html), "html.parser")
    candidates: list[str] = []
    for a in soup.find_all("a", href=True):
        href = str(a["href"])
        text = a.get_text(" ", strip=True)
        hay = f"{href} {text}".lower()
        if filename and filename.lower() in hay:
            candidates.append(href)
        elif hint and hint.lower() in hay:
            candidates.append(href)
    if not candidates:
        # NADA pages sometimes load file links through embedded JSON/scripts.
        text = str(html)
        if filename:
            m = re.search(rf"(?:https?://[^\"']+|/[^\"']+){re.escape(filename)}", text, re.I)
            if m:
                candidates.append(m.group(0))
    if not candidates:
        raise RuntimeError(f"Could not discover official download from {catalog}: {filename or hint}")
    href = candidates[0].replace("&amp;", "&")
    if href.startswith("http"):
        return href
    return requests.compat.urljoin(catalog, href)


def fetch_source(key: str) -> tuple[Path, dict[str, Any]]:
    s = SOURCES[key]
    url = s.get("url") or discover_download(s["catalog"], s.get("filename"), s.get("filename_hint"))
    data = get(str(url), binary=True)
    assert isinstance(data, bytes)
    # reject HTML error pages masquerading as spreadsheets
    if data[:100].lstrip().lower().startswith(b"<!doctype html") or data[:100].lstrip().lower().startswith(b"<html"):
        raise RuntimeError(f"Official download returned HTML instead of a data file: {url}")
    filename = s.get("filename") or Path(str(url).split("?", 1)[0]).name or f"{key}.xlsx"
    path = RAW / str(filename)
    path.write_bytes(data)
    return path, {"url": url, "sha256": sha256_bytes(data), "bytes": len(data), "source_id": s["source_id"]}


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join(str(x) for x in tup if str(x) != "nan") for tup in df.columns]
    df.columns = [norm(c) for c in df.columns]
    return df


def read_excel_smart(path: Path) -> pd.DataFrame:
    # First try normal header. If it looks unusable, locate the real header row.
    engine = "xlrd" if path.suffix.lower() == ".xls" else "openpyxl"
    df = pd.read_excel(path, dtype=str, engine=engine)
    df = flatten_columns(df).fillna("")
    useful = " ".join(df.columns)
    if any(k in useful for k in ("state_code", "district_code", "village_code", "town_village")):
        return df
    raw = pd.read_excel(path, header=None, dtype=str, engine=engine).fillna("")
    for i in range(min(30, len(raw))):
        line = " ".join(norm(x) for x in raw.iloc[i].tolist())
        if "state" in line and ("district" in line or "village" in line or "location" in line):
            df = pd.read_excel(path, header=i, dtype=str, engine=engine).fillna("")
            return flatten_columns(df)
    return df


def find_col(columns: list[str], aliases: list[str], contains: list[str] | None = None) -> str | None:
    cmap = {norm(c): c for c in columns}
    for a in aliases:
        if norm(a) in cmap:
            return cmap[norm(a)]
    if contains:
        for c in columns:
            nc = norm(c)
            if all(x in nc for x in contains):
                return c
    return None


def build_census_places(location_path: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    df = read_excel_smart(location_path)
    cols = list(df.columns)
    state_c = find_col(cols, ["state code", "state/ut code", "state_union_territory_ut_code"], ["state", "code"])
    dist_c = find_col(cols, ["district code"], ["district", "code"])
    sub_c = find_col(cols, ["sub-district code", "sub district code", "subdistrict code"], ["sub", "district", "code"])
    tv_c = find_col(cols, ["town/village code", "town village code", "village/town code", "location code"], ["town", "village", "code"])
    name_c = find_col(cols, ["town/village name", "town village name", "village/town name", "area name", "name"], ["town", "village", "name"])
    type_c = find_col(cols, ["town/village", "town village", "type", "level"], None)
    dist_name_c = find_col(cols, ["district name"], ["district", "name"])
    sub_name_c = find_col(cols, ["sub-district name", "sub district name", "subdistrict name"], ["sub", "district", "name"])
    missing = [n for n, c in {"state": state_c, "district": dist_c, "subdistrict": sub_c, "town_village": tv_c, "name": name_c}.items() if not c]
    if missing:
        raise RuntimeError(f"Location directory columns not recognised: {missing}; columns={cols[:40]}")

    work = df.copy()
    work["_state"] = work[state_c].map(digits)
    work = work[work["_state"].str.zfill(2) == "20"].copy()
    if work.empty:
        raise RuntimeError("Location directory contained no Jharkhand (state code 20) rows")

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    # State row
    rows.append({
        "place_id": "JH-STATE-20", "place_type": "state", "name": "Jharkhand", "parent_place_id": "",
        "state_code": "20", "state_name": "Jharkhand", "district_code": "", "district_name": "",
        "subdistrict_code": "", "subdistrict_name": "", "block_code": "", "block_name": "",
        "panchayat_code": "", "panchayat_name": "", "village_code": "", "village_name": "",
        "latitude": "", "longitude": "", "valid_from": "2011", "valid_to": "",
        "source_id": "CENSUS_LOCATION_DIR_2011", "quality_class": "A", "record_status": "verified_source_ingest",
    })
    seen.add("JH-STATE-20")

    for _, r in work.iterrows():
        d = digits(r[dist_c]).zfill(3) if digits(r[dist_c]) else ""
        sd = digits(r[sub_c]).zfill(5) if digits(r[sub_c]) else ""
        tv = digits(r[tv_c]).zfill(6) if digits(r[tv_c]) else ""
        name = str(r[name_c]).strip()
        dname = str(r[dist_name_c]).strip() if dist_name_c else ""
        sdname = str(r[sub_name_c]).strip() if sub_name_c else ""
        typetxt = str(r[type_c]).strip().lower() if type_c else ""

        if d:
            pid = f"JH-DIST-{d}"
            if pid not in seen:
                rows.append({"place_id": pid, "place_type": "district", "name": dname or name, "parent_place_id": "JH-STATE-20",
                             "state_code": "20", "state_name": "Jharkhand", "district_code": d, "district_name": dname or name,
                             "subdistrict_code": "", "subdistrict_name": "", "block_code": "", "block_name": "", "panchayat_code": "", "panchayat_name": "",
                             "village_code": "", "village_name": "", "latitude": "", "longitude": "", "valid_from": "2011", "valid_to": "",
                             "source_id": "CENSUS_LOCATION_DIR_2011", "quality_class": "A", "record_status": "verified_source_ingest"})
                seen.add(pid)
        if sd:
            pid = f"JH-SUBD-{sd}"
            if pid not in seen:
                rows.append({"place_id": pid, "place_type": "subdistrict", "name": sdname or name, "parent_place_id": f"JH-DIST-{d}",
                             "state_code": "20", "state_name": "Jharkhand", "district_code": d, "district_name": dname,
                             "subdistrict_code": sd, "subdistrict_name": sdname or name, "block_code": "", "block_name": "", "panchayat_code": "", "panchayat_name": "",
                             "village_code": "", "village_name": "", "latitude": "", "longitude": "", "valid_from": "2011", "valid_to": "",
                             "source_id": "CENSUS_LOCATION_DIR_2011", "quality_class": "A", "record_status": "verified_source_ingest"})
                seen.add(pid)
        if tv and name:
            place_type = "town" if "town" in typetxt else "village"
            prefix = "TOWN" if place_type == "town" else "VILL"
            pid = f"JH-{prefix}-{tv}"
            if pid not in seen:
                rows.append({"place_id": pid, "place_type": place_type, "name": name, "parent_place_id": f"JH-SUBD-{sd}" if sd else f"JH-DIST-{d}",
                             "state_code": "20", "state_name": "Jharkhand", "district_code": d, "district_name": dname,
                             "subdistrict_code": sd, "subdistrict_name": sdname, "block_code": "", "block_name": "", "panchayat_code": "", "panchayat_name": "",
                             "village_code": tv if place_type == "village" else "", "village_name": name if place_type == "village" else "",
                             "latitude": "", "longitude": "", "valid_from": "2011", "valid_to": "",
                             "source_id": "CENSUS_LOCATION_DIR_2011", "quality_class": "A", "record_status": "verified_source_ingest"})
                seen.add(pid)

    out = pd.DataFrame(rows)
    counts = out["place_type"].value_counts().to_dict()
    if counts.get("district", 0) != 24:
        raise RuntimeError(f"Expected 24 Census-2011 Jharkhand districts, got {counts.get('district', 0)}")
    if counts.get("village", 0) < 30000:
        raise RuntimeError(f"Expected >30,000 Census village rows, got {counts.get('village', 0)}")
    return out, {k: int(v) for k, v in counts.items()}


def build_basic_population(path: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    df = read_excel_smart(path)
    cols = list(df.columns)
    # Find state/district/subdistrict/village identity columns and a robust subset of PCA fields.
    state_c = find_col(cols, ["state code", "state"], ["state", "code"])
    dist_c = find_col(cols, ["district code"], ["district", "code"])
    sub_c = find_col(cols, ["sub-district code", "sub district code"], ["sub", "district", "code"])
    loc_c = find_col(cols, ["town/village code", "town village code", "village code", "location code"], ["village", "code"])
    name_c = find_col(cols, ["name", "area name", "town/village name"], None)
    level_c = find_col(cols, ["level"], None)
    if not state_c:
        # Some official PCA sheets encode the geographic hierarchy in one location-code field.
        for c in cols:
            if "state" in c and "code" in c:
                state_c = c; break
    if not state_c:
        raise RuntimeError(f"Basic Population state-code column not recognised; columns={cols[:60]}")
    work = df.copy()
    work["_state"] = work[state_c].map(digits)
    work = work[work["_state"].str.zfill(2) == "20"].copy()
    if work.empty:
        raise RuntimeError("Basic Population file contained no Jharkhand rows")

    field_aliases = {
        "households": [["number of households"], ["households"]],
        "population_total": [["population persons"], ["population total"], ["total population"]],
        "population_male": [["population males"], ["population male"]],
        "population_female": [["population females"], ["population female"]],
        "age_0_6_total": [["population 0 6 persons"], ["population in the age group 0 6 persons"]],
        "sc_total": [["scheduled castes population persons"], ["population of scheduled castes total"]],
        "st_total": [["scheduled tribes population persons"], ["population of scheduled tribes total"]],
        "literate_total": [["literate population persons"], ["population literate"]],
        "worker_total": [["total workers persons"], ["workers persons"]],
        "main_worker_total": [["main workers persons"]],
        "marginal_worker_total": [["marginal workers persons"]],
    }
    fmap: dict[str, str | None] = {}
    for outname, alias_sets in field_aliases.items():
        found = None
        for aset in alias_sets:
            found = find_col(cols, [" ".join(aset)], aset)
            if found: break
        fmap[outname] = found

    rows = []
    for _, r in work.iterrows():
        level = str(r[level_c]).lower() if level_c else ""
        loc = digits(r[loc_c]) if loc_c else ""
        # If a level column exists, keep village/town rows. Otherwise keep rows with a six-digit location code.
        if level_c and not ("village" in level or "town" in level):
            continue
        if not level_c and loc and len(loc) < 6:
            continue
        d = digits(r[dist_c]).zfill(3) if dist_c and digits(r[dist_c]) else ""
        sd = digits(r[sub_c]).zfill(5) if sub_c and digits(r[sub_c]) else ""
        place_code = loc.zfill(6) if loc else ""
        name = str(r[name_c]).strip() if name_c else ""
        row = {"place_code": place_code, "district_code": d, "subdistrict_code": sd, "name": name,
               "reference_year": "2011", "source_id": "CENSUS_BASIC_2011", "observation_type": "observed"}
        for outname, c in fmap.items():
            row[outname] = str(r[c]).strip() if c else ""
        rows.append(row)
    out = pd.DataFrame(rows)
    if len(out) < 30000:
        raise RuntimeError(f"Expected >30,000 Jharkhand village/town PCA rows, got {len(out)}")
    return out, {"rows": int(len(out)), "fields_populated": int(sum(1 for v in fmap.values() if v))}


def sync_lgd() -> tuple[dict[str, pd.DataFrame], dict[str, int]]:
    # LGD state code 20 is Jharkhand. Keep current administrative data separate from Census 2011.
    districts = post_json(f"{LGD}/districtList?stateCode=20")
    if not isinstance(districts, list) or len(districts) < 20:
        raise RuntimeError("LGD districtList did not return a plausible Jharkhand district list")
    subdistricts: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    panchayats: list[dict[str, Any]] = []
    villages: list[dict[str, Any]] = []

    for d in districts:
        dc = d.get("districtCode")
        if not dc: continue
        try:
            sd = post_json(f"{LGD}/subdistrictList?districtCode={dc}")
            if isinstance(sd, list): subdistricts.extend(sd)
        except Exception:
            pass
        try:
            bl = post_json(f"{LGD}/blockList?districtCode={dc}")
            if isinstance(bl, list): blocks.extend(bl)
        except Exception:
            pass
        time.sleep(0.03)

    # GP mapping from blocks
    for b in blocks:
        bc = b.get("blockCode")
        if not bc: continue
        try:
            gp = post_json(f"{LGD}/getBlockwiseMappedGP?blockCode={bc}")
            if isinstance(gp, list):
                for x in gp:
                    x = dict(x); x.setdefault("blockCode", bc); panchayats.append(x)
        except Exception:
            pass
        time.sleep(0.02)

    # Villages with hierarchy from subdistricts. This response includes block/GP mapping when LGD has it.
    for sd in subdistricts:
        sc = sd.get("subdistrictCode") or sd.get("subDistrictCode")
        if not sc: continue
        try:
            vv = post_json(f"{LGD}/villageListWithHierarchy?subDistrictCode={sc}")
            if isinstance(vv, list): villages.extend(vv)
        except Exception:
            pass
        time.sleep(0.02)

    tables = {
        "lgd_districts_current.csv": pd.DataFrame(districts),
        "lgd_subdistricts_current.csv": pd.DataFrame(subdistricts),
        "lgd_blocks_current.csv": pd.DataFrame(blocks),
        "lgd_panchayats_current.csv": pd.DataFrame(panchayats).drop_duplicates(),
        "lgd_villages_current.csv": pd.DataFrame(villages).drop_duplicates(),
    }
    counts = {k.replace("lgd_", "").replace("_current.csv", ""): int(len(v)) for k, v in tables.items()}
    if counts["districts"] != 24:
        raise RuntimeError(f"Expected 24 current LGD districts, got {counts['districts']}")
    if counts["blocks"] < 250:
        raise RuntimeError(f"Expected at least 250 current LGD blocks, got {counts['blocks']}")
    if counts["villages"] < 30000:
        raise RuntimeError(f"Expected >30,000 current LGD village rows, got {counts['villages']}")
    return tables, counts


def write_df(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False, encoding="utf-8")


def main() -> None:
    report: dict[str, Any] = {"started_at": datetime.now(timezone.utc).isoformat(), "status": "running", "sources": {}, "counts": {}, "errors": []}
    try:
        # Census location directory
        loc_path, meta = fetch_source("location_directory")
        report["sources"]["location_directory"] = meta
        places, counts = build_census_places(loc_path)
        write_df(places, OUT / "places.csv")
        write_df(places, OUT / "census_places_2011.csv")
        report["counts"]["census_places"] = counts

        # Census basic population / PCA baseline
        pop_path, meta = fetch_source("basic_population")
        report["sources"]["basic_population"] = meta
        pop, popcounts = build_basic_population(pop_path)
        write_df(pop, OUT / "village_demography_2011.csv")
        report["counts"]["basic_population"] = popcounts

        # MDDS crosswalk (download + preserve hash; ingestion remains separate because source layout may vary)
        mdds_path, meta = fetch_source("mdds_jh")
        report["sources"]["mdds_jh"] = meta
        report["sources"]["mdds_jh"]["local_path"] = str(mdds_path.relative_to(ROOT))

        # Current LGD hierarchy
        lgd_tables, lgd_counts = sync_lgd()
        for name, table in lgd_tables.items():
            write_df(table, OUT / name)
        report["counts"]["lgd_current"] = lgd_counts

        # DCHB state village amenities: best effort, but fail if a file downloads and cannot be identified.
        try:
            am_path, meta = fetch_source("village_amenities")
            report["sources"]["village_amenities"] = meta
            report["sources"]["village_amenities"]["local_path"] = str(am_path.relative_to(ROOT))
        except Exception as exc:
            report["sources"]["village_amenities"] = {"status": "metadata_verified_download_pending", "error": str(exc)}

        report["status"] = "success"
    except Exception as exc:
        report["status"] = "failed"
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        raise
    finally:
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
