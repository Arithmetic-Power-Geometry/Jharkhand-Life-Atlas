#!/usr/bin/env python3
"""Inventory source-native Census 2011 amenity fields for priority JLA modules.

This script does not publish thematic observations. It inspects the exact header
of the already-governed Module 1 DCHB village-amenities table and records fields
whose source-native names match conservative domain tokens. The resulting JSON
is an observed-schema aid for later explicit review and projection; token
matching itself is never treated as evidence that a field is publishable.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

SOURCE = Path("data/curated/core_geography/village_amenities_2011.csv")
OUTPUT = Path("modules/core_geography/amenity_domain_field_inventory.json")

IDENTITY_OR_PROVENANCE = {
    "state_code", "state_name", "district_code", "district_name",
    "sub_district_code", "sub_district_name", "village_code", "village_name",
    "cd_block_code", "cd_block_name", "gram_panchayat_code",
    "gram_panchayat_name", "reference_year", "place_id", "source_id",
    "observation_type", "quality_class", "source_sha256", "source_file",
    "source_sheet", "source_code_column",
}

DOMAIN_TOKENS = {
    "water_access": (
        "drinking_water", "tap_water", "piped_water", "hand_pump", "handpump",
        "tube_well", "tubewell", "covered_well", "uncovered_well", "water_tank",
        "tank_pond", "spring", "river_canal", "water_source",
    ),
    "sanitation_hygiene": (
        "latrine", "toilet", "sanitation", "sewer", "drain", "waste_water",
        "wastewater", "garbage", "solid_waste", "liquid_waste", "bathroom",
        "community_toilet",
    ),
    "education_access": (
        "school", "college", "education", "literacy_centre", "literacy_center",
        "vocational_training", "training_school",
    ),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)

    with SOURCE.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
    if not header:
        raise ValueError("Governed village-amenities table has no header")
    if len(header) != len(set(header)):
        raise ValueError("Governed village-amenities table contains duplicate headers")

    candidates: dict[str, list[str]] = {}
    for domain, tokens in DOMAIN_TOKENS.items():
        matched = [
            field for field in header
            if field not in IDENTITY_OR_PROVENANCE
            and any(token in field.lower() for token in tokens)
        ]
        if not matched:
            raise ValueError(f"No observed source fields matched conservative tokens for {domain}")
        candidates[domain] = matched

    payload = {
        "status": "observed_schema_inventory_not_publication_approval",
        "source": str(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "source_field_count": len(header),
        "domains": {
            domain: {
                "match_tokens": list(DOMAIN_TOKENS[domain]),
                "candidate_field_count": len(fields),
                "candidate_fields": fields,
                "review_rule": (
                    "Every candidate must be explicitly reviewed against source semantics before "
                    "thematic projection; token matching alone never authorizes publication."
                ),
            }
            for domain, fields in candidates.items()
        },
        "geography_rule": "Census 2011 source-native geography only; no current-geography equivalence inferred",
        "missing_rule": "schema inventory performs no value coercion and cannot authorize missing-to-zero conversion",
        "publication_rule": "inventory is metadata only; no thematic dataset is published by this script",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({d: len(v) for d, v in candidates.items()}, sort_keys=True))


if __name__ == "__main__":
    main()
