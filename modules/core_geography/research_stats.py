"""Recompute manuscript-supporting Module 1 statistics from curated artifacts.

This script is intentionally descriptive only: it does not infer historical/current
administrative equivalence and does not alter missing values.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CURATED = ROOT / "data" / "curated" / "core_geography"


def _rows(name: str) -> int:
    return int(len(pd.read_csv(CURATED / name, low_memory=False)))


def _unique_nonnull(name: str, column: str) -> int:
    frame = pd.read_csv(CURATED / name, usecols=[column], dtype={column: "string"})
    return int(frame[column].dropna().nunique())


def build_statistics() -> dict:
    """Return reproducible descriptive statistics from version-pinned CSV artifacts."""
    census = pd.read_csv(
        CURATED / "census_places_2011.csv",
        usecols=["place_type", "district_code", "subdistrict_code", "village_code"],
        dtype="string",
        low_memory=False,
    )
    place_counts = {
        str(k): int(v)
        for k, v in census["place_type"].dropna().value_counts().sort_index().items()
    }

    return {
        "census_2011": {
            "place_rows": int(len(census)),
            "place_type_rows": place_counts,
            "district_codes": int(census["district_code"].dropna().nunique()),
            "subdistrict_codes": int(census["subdistrict_code"].dropna().nunique()),
            "village_codes": int(census["village_code"].dropna().nunique()),
            "village_demography_rows": _rows("village_demography_2011.csv"),
            "village_amenities_rows": _rows("village_amenities_2011.csv"),
        },
        "current_lgd": {
            "district_rows": _rows("lgd_districts_current.csv"),
            "subdistrict_rows": _rows("lgd_subdistricts_current.csv"),
            "block_rows": _rows("lgd_blocks_current.csv"),
            "panchayat_rows": _rows("lgd_panchayats_current.csv"),
            "village_rows": _rows("lgd_villages_current.csv"),
        },
        "crosswalks": {
            "census_2001_2011_rows": _rows("census_mdds_crosswalk_2001_2011.csv"),
            "census_2011_lgd_temporal_rows": _rows("census_lgd_temporal_crosswalk.csv"),
        },
        "integrity": {
            "missing_values_preserved": True,
            "name_only_temporal_equivalence_inferred": False,
            "person_level_data_used": False,
        },
    }


def main() -> None:
    print(json.dumps(build_statistics(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
