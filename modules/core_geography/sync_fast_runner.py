"""Faster runner for Module 1: parallel official PCA-TV acquisition.

Imports all safety/compatibility rules from sync_runner, then replaces only the
24-district PCA acquisition step with bounded parallel downloads. Parsing and all
hard validation rules remain unchanged.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

import sync_runner as base

sync = base.sync


def _fetch_one(seq: int):
    ref = f"20{seq:02d}"
    catalog_id = 6536 + seq
    filename = f"DDW_PCA{ref}_2011_MDDS with UI.xlsx"
    catalog = f"https://censusindia.gov.in/nada/index.php/catalog/{catalog_id}"
    url = sync.discover_download(catalog, filename=filename)
    data = sync.get(url, binary=True)
    if not isinstance(data, bytes) or len(data) < 10_000:
        raise RuntimeError(f"Implausible PCA-TV download for {ref}: {url}")
    path = sync.RAW / filename
    path.write_bytes(data)
    part = base._parse_pca_tv(path)
    if part.empty:
        raise RuntimeError(f"No village/town rows parsed from official PCA-TV {ref}")
    meta = {
        "reference_id": f"PC11_PCA-TV-{ref}",
        "catalog_id": catalog_id,
        "filename": filename,
        "url": url,
        "sha256": sync.sha256_bytes(data),
        "bytes": len(data),
        "rows_parsed": len(part),
    }
    return seq, part, meta


def build_population(_unused_national_path):
    results = {}
    # Bounded concurrency reduces load on Census NADA while avoiding ~24 serial waits.
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(_fetch_one, seq): seq for seq in range(1, 25)}
        for future in as_completed(futures):
            seq, part, meta = future.result()
            results[seq] = (part, meta)
            print(f"PCA-TV 20{seq:02d}: {len(part)} whole-place rows")

    if set(results) != set(range(1, 25)):
        missing = sorted(set(range(1, 25)) - set(results))
        raise RuntimeError(f"Missing PCA-TV district workbooks: {missing}")

    frames = [results[i][0] for i in range(1, 25)]
    manifest = [results[i][1] for i in range(1, 25)]
    out = pd.concat(frames, ignore_index=True)
    out = out.drop_duplicates(subset=["place_code", "name"], keep="first")
    if len(out) < 30_000:
        raise RuntimeError(f"Expected >30,000 Jharkhand PCA-TV place rows, got {len(out)}")

    core = ["households", "population_total", "population_male", "population_female",
            "age_0_6_total", "sc_total", "st_total", "literate_total", "worker_total"]
    populated = sum(1 for c in core if c in out.columns and (out[c].astype(str).str.strip() != "").any())
    if populated < 8:
        raise RuntimeError(f"PCA-TV demographic parsing too sparse: only {populated} core fields populated")

    pd.DataFrame(manifest).to_csv(sync.OUT / "pca_source_manifest_2011.csv", index=False)
    return out, {"rows": int(len(out)), "district_workbooks": 24, "core_fields_populated": int(populated)}


sync.build_basic_population = build_population

if __name__ == "__main__":
    sync.main()
