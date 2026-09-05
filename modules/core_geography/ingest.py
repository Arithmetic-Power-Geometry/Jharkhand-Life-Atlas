"""Auditable Core Geography ingestion utilities.

This module never downloads an unverified mirror and never invents geographic
codes. It converts reviewed official Census/LGD exports into JLA's canonical
CSV tables. Raw source files belong in ``data/raw/core_geography/`` and are not
committed unless their redistribution terms explicitly allow it.

Supported inputs:
* CSV natively.
* XLS/XLSX when pandas plus the appropriate Excel engine are installed.

Examples
--------
python modules/core_geography/ingest.py village-directory data/raw/core_geography/Rdir_2001_MDDS_20.xls
python modules/core_geography/ingest.py pca data/raw/core_geography/pca_jharkhand.xlsx
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "core_geography"
OUT = ROOT / "data" / "curated" / "core_geography"


def _norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _read(path: Path) -> list[dict[str, object]]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    try:
        import pandas as pd  # optional ingestion dependency, not required by the app
    except ImportError as exc:
        raise SystemExit("Excel ingestion requires pandas and an Excel engine (openpyxl for xlsx; xlrd for xls). Convert the official file to CSV or install them locally.") from exc
    return pd.read_excel(path, dtype=str).fillna("").to_dict("records")


def _pick(row: dict[str, object], *aliases: str) -> str:
    normalized = {_norm(k): "" if v is None else str(v).strip() for k, v in row.items()}
    for alias in aliases:
        key = _norm(alias)
        if key in normalized and normalized[key] != "":
            return normalized[key]
    return ""


def _digits(value: str) -> str:
    m = re.search(r"\d+", value or "")
    return m.group(0) if m else ""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def ingest_village_directory(path: Path) -> dict[str, object]:
    raw = _read(path)
    out = []
    for r in raw:
        state = _digits(_pick(r, "state code", "slrc", "state"))
        if state and state.zfill(2) != "20":
            continue
        district = _digits(_pick(r, "district code", "dlrc", "district"))
        subdistrict = _digits(_pick(r, "sub district code", "sub-district code", "sdlrc", "subdistrict"))
        village = _digits(_pick(r, "village code", "vlrc", "village"))
        name = _pick(r, "village name", "village name in english", "vne", "name")
        if not village or not name:
            continue
        out.append({
            "place_id": f"JH-VILL-{village.zfill(6)}",
            "place_type": "village",
            "name": name,
            "state_code": "20",
            "district_code": district,
            "district_name": _pick(r, "district name"),
            "subdistrict_code": subdistrict,
            "subdistrict_name": _pick(r, "sub district name", "sub-district name", "subdistrict name"),
            "village_code": village.zfill(6),
            "village_name": name,
            "census_2001_village_code": _digits(_pick(r, "2001 village code", "village code 2001", "village code (2001)")),
            "source_id": "CENSUS_MDDS_JH_2011",
            "quality_class": "A",
            "record_status": "verified_source_ingest",
        })
    if not out:
        raise SystemExit("No Jharkhand village rows recognized. Inspect source headers; no output was overwritten.")
    codes = [r["village_code"] for r in out]
    if len(codes) != len(set(codes)):
        raise SystemExit("Duplicate Census village codes detected; ingestion aborted.")
    fields = list(out[0])
    write_csv(OUT / "census_villages_2011.csv", out, fields)
    return {"input": str(path), "sha256": sha256(path), "rows": len(out), "output": "census_villages_2011.csv"}


def ingest_pca(path: Path) -> dict[str, object]:
    raw = _read(path)
    out=[]
    for r in raw:
        state = _digits(_pick(r, "state", "state code"))
        if state and state.zfill(2) != "20":
            continue
        level = _pick(r, "level").lower()
        if level and "village" not in level:
            continue
        village = _digits(_pick(r, "town/village", "town village", "village code", "location code"))
        if not village:
            continue
        def val(*a): return _pick(r, *a)
        out.append({
            "village_code": village.zfill(6),
            "name": val("name"),
            "households": val("no_hh", "number of households", "households"),
            "population_total": val("tot_p", "population persons", "total population"),
            "population_male": val("tot_m", "population males"),
            "population_female": val("tot_f", "population females"),
            "age_0_6_total": val("p_06", "population in the age group 0-6 persons"),
            "sc_total": val("p_sc", "scheduled castes population persons"),
            "st_total": val("p_st", "scheduled tribes population persons"),
            "literate_total": val("p_lit", "literate population persons"),
            "worker_total": val("p_work", "total workers persons"),
            "main_worker_total": val("mainwork_p", "main workers persons"),
            "marginal_worker_total": val("margwork_p", "marginal workers persons"),
            "source_id": "OGD_PCA_JH_2011",
            "reference_year": "2011",
            "observation_type": "observed",
        })
    if not out:
        raise SystemExit("No Jharkhand village PCA rows recognized. No output was overwritten.")
    write_csv(OUT / "village_demography_2011.csv", out, list(out[0]))
    return {"input": str(path), "sha256": sha256(path), "rows": len(out), "output": "village_demography_2011.csv"}


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("kind", choices=["village-directory","pca"])
    p.add_argument("file", type=Path)
    a=p.parse_args()
    if not a.file.exists(): raise SystemExit(f"File not found: {a.file}")
    result = ingest_village_directory(a.file) if a.kind == "village-directory" else ingest_pca(a.file)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
