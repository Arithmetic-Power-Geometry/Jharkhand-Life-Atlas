"""Generate reproducible manuscript-supporting inputs for Module 1.

Outputs are descriptive release-support assets only. Historical Census 2011 and current
LGD counts are kept as separate vintages; this module never treats equal/similar names or
counts as evidence of administrative equivalence.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from modules.core_geography.research_stats import build_statistics


def build_geography_count_rows(stats: dict) -> list[dict[str, object]]:
    """Return long-form counts with explicit vintage and comparability semantics."""
    census = stats["census_2011"]
    current = stats["current_lgd"]
    rows = [
        ("census_2011", "district", census["district_codes"]),
        ("census_2011", "subdistrict", census["subdistrict_codes"]),
        ("census_2011", "village", census["village_codes"]),
        ("current_lgd", "district", current["district_rows"]),
        ("current_lgd", "subdistrict", current["subdistrict_rows"]),
        ("current_lgd", "block", current["block_rows"]),
        ("current_lgd", "panchayat", current["panchayat_rows"]),
        ("current_lgd", "village", current["village_rows"]),
    ]
    return [
        {
            "geography_vintage": vintage,
            "unit_type": unit_type,
            "count": int(count),
            "cross_vintage_equivalence_asserted": False,
        }
        for vintage, unit_type, count in rows
    ]


def build_table_rows(stats: dict) -> list[dict[str, object]]:
    """Return table-ready verified descriptive statistics without imputing missing data."""
    census = stats["census_2011"]
    current = stats["current_lgd"]
    crosswalks = stats["crosswalks"]
    return [
        {"section": "Census 2011", "metric": "place rows", "value": census["place_rows"]},
        {"section": "Census 2011", "metric": "district codes", "value": census["district_codes"]},
        {"section": "Census 2011", "metric": "subdistrict codes", "value": census["subdistrict_codes"]},
        {"section": "Census 2011", "metric": "village codes", "value": census["village_codes"]},
        {"section": "Census 2011", "metric": "village demography rows", "value": census["village_demography_rows"]},
        {"section": "Census 2011", "metric": "village amenities rows", "value": census["village_amenities_rows"]},
        {"section": "Current LGD", "metric": "district rows", "value": current["district_rows"]},
        {"section": "Current LGD", "metric": "subdistrict rows", "value": current["subdistrict_rows"]},
        {"section": "Current LGD", "metric": "block rows", "value": current["block_rows"]},
        {"section": "Current LGD", "metric": "panchayat rows", "value": current["panchayat_rows"]},
        {"section": "Current LGD", "metric": "village rows", "value": current["village_rows"]},
        {"section": "Crosswalk", "metric": "Census 2001-2011 rows", "value": crosswalks["census_2001_2011_rows"]},
        {"section": "Crosswalk", "metric": "Census 2011-LGD temporal rows", "value": crosswalks["census_2011_lgd_temporal_rows"]},
    ]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("research asset rows must not be empty")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_assets(output_dir: Path) -> dict[str, Path]:
    """Write deterministic JSON/CSV inputs derived only from curated Module 1 artifacts."""
    stats = build_statistics()
    output_dir.mkdir(parents=True, exist_ok=True)

    stats_path = output_dir / "manuscript_statistics.json"
    stats_path.write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    table_path = output_dir / "table_descriptive_statistics.csv"
    _write_csv(table_path, build_table_rows(stats))

    figure_path = output_dir / "figure_geography_counts_long.csv"
    _write_csv(figure_path, build_geography_count_rows(stats))

    methods_path = output_dir / "asset_semantics.json"
    methods_path.write_text(
        json.dumps(
            {
                "missing_values_imputed": False,
                "cross_vintage_equivalence_inferred": False,
                "person_level_data_used": False,
                "figure_rule": "Plot vintages as explicitly distinct series/panels; do not imply one-to-one administrative continuity.",
                "source": "version-pinned curated Module 1 CSV artifacts",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "statistics": stats_path,
        "table": table_path,
        "figure": figure_path,
        "semantics": methods_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/research/core_geography"),
        help="Directory for reproducible manuscript-supporting inputs.",
    )
    args = parser.parse_args()
    paths = write_assets(args.output_dir)
    print(json.dumps({k: str(v) for k, v in paths.items()}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
