#!/usr/bin/env python3
"""Build validated source-native Census 2011 extracts for Modules 3–5.

The source is the already-governed Module 1 DCHB village-amenities table.
Fields are an explicit reviewed subset of the observed schema inventory. No
current-geography remapping, imputation, missing-to-zero conversion, semantic
recoding, aggregation, or availability derivation is performed.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

SOURCE = Path("data/curated/core_geography/village_amenities_2011.csv")
INVENTORY = Path("modules/core_geography/amenity_domain_field_inventory.json")

IDENTITY_FIELDS = [
    "state_code", "state_name", "district_code", "district_name",
    "sub_district_code", "sub_district_name", "village_code", "village_name",
    "cd_block_code", "cd_block_name", "gram_panchayat_code",
    "gram_panchayat_name", "reference_year",
]

DOMAIN_FIELDS = {
    "water_access": [
        "tap_water_treated_status_a_1_na_2",
        "tap_water_treated_functioning_all_round_the_year_status_a_1_na_2",
        "tap_water_treated_functioning_in_summer_months_april_september_status_a_1_na_2",
        "tap_water_untreated_status_a_1_na_2",
        "tap_water_untreated_functioning_all_round_the_year_status_a_1_na_2",
        "tap_water_untreated_functioning_in_summer_months_april_september_status_a_1_na_2",
        "covered_well_status_a_1_na_2",
        "covered_well_functioning_all_round_the_year_status_a_1_na_2",
        "covered_well_functioning_in_summer_months_april_september_status_a_1_na_2",
        "uncovered_well_status_a_1_na_2",
        "uncovered_well_functioning_all_round_the_year_status_a_1_na_2",
        "uncovered_well_functioning_in_summer_months_april_september_status_a_1_na_2",
        "hand_pump_status_a_1_na_2",
        "hand_pump_functioning_all_round_the_year_status_a_1_na_2",
        "hand_pump_functioning_in_summer_months_april_september_status_a_1_na_2",
        "tube_wells_borehole_status_a_1_na_2",
        "tube_wells_borehole_functioning_all_round_the_year_status_a_1_na_2",
        "tube_wells_borehole_functioning_in_summer_months_april_september_status_a_1_na_2",
        "spring_status_a_1_na_2",
        "spring_functioning_all_round_the_year_status_a_1_na_2",
        "spring_functioning_in_summer_months_april_september_status_a_1_na_2",
        "river_canal_status_a_1_na_2",
        "river_canal_functioning_all_round_the_year_status_a_1_na_2",
        "river_canal_functioning_in_summer_months_april_september_status_a_1_na_2",
        "tank_pond_lake_status_a_1_na_2",
        "tank_pond_lake_functioning_all_round_the_year_status_a_1_na_2",
        "tank_pond_lake_functioning_in_summer_months_april_september_status_a_1_na_2",
    ],
    "sanitation_hygiene": [
        "closed_drainage_status_a_1_na_2",
        "open_drainage_status_a_1_na_2",
        "no_drainage_status_a_1_na_2",
        "open_pucca_drainage_covered_with_tiles_slabs_status_a_1_na_2",
        "open_pucca_drainage_uncovered_status_a_1_na_2",
        "open_kuccha_drainage_status_a_1_na_2",
        "whether_drain_water_is_discharged_directly_into_water_bodies_or_to_sewar_plant_for_water_bodies_1_sewar_plants_2",
        "is_the_area_covered_under_total_sanitation_campaign_tsc_status_a_1_na_2",
        "community_toilet_complex_including_bath_for_general_public_status_a_1_na_2",
        "community_toilet_complex_excluding_bath_for_general_public_status_a_1_na_2",
        "no_system_garbage_on_road_street_status_a_1_na_2",
    ],
    "education_access": [
        "govt_pre_primary_school_nursery_lkg_ukg_status_a_1_na_2",
        "govt_pre_primary_school_nursery_lkg_ukg_numbers",
        "private_pre_primary_school_nursery_lkg_ukg_status_a_1_na_2",
        "private_pre_primary_school_nursery_lkg_ukg_numbers",
        "govt_primary_school_status_a_1_na_2", "govt_primary_school_numbers",
        "private_primary_school_status_a_1_na_2", "private_primary_school_numbers",
        "govt_middle_school_status_a_1_na_2", "govt_middle_school_numbers",
        "private_middle_school_status_a_1_na_2", "private_middle_school_numbers",
        "govt_secondary_school_status_a_1_na_2", "govt_secondary_school_numbers",
        "private_secondary_school_status_a_1_na_2", "private_secondary_school_numbers",
        "govt_senior_secondary_school_status_a_1_na_2", "govt_senior_secondary_school_numbers",
        "private_senior_secondary_school_status_a_1_na_2", "private_senior_secondary_school_numbers",
        "govt_arts_and_science_degree_college_status_a_1_na_2", "govt_arts_and_science_degree_college_numbers",
        "private_arts_and_science_degree_college_status_a_1_na_2", "private_arts_and_science_degree_college_numbers",
        "govt_engineering_college_status_a_1_na_2", "govt_engineering_college_numbers",
        "private_engineering_college_status_a_1_na_2", "private_engineering_college_numbers",
        "govt_medicine_college_status_a_1_na_2", "govt_medicine_college_numbers",
        "private_medicine_college_status_a_1_na_2", "private_medicine_college_numbers",
        "govt_vocational_training_school_iti_status_a_1_na_2", "govt_vocational_training_school_iti_numbers",
        "private_vocational_training_school_iti_status_a_1_na_2", "private_vocational_training_school_iti_numbers",
        "government_school_for_disabled_status_a_1_na_2", "government_school_for_disabled_numbers",
        "private_school_for_disabled_status_a_1_na_2", "private_school_for_disabled_numbers",
    ],
}

OUTPUTS = {
    "water_access": Path("data/curated/water_access/census_water_access_2011.csv"),
    "sanitation_hygiene": Path("data/curated/sanitation_hygiene/census_sanitation_hygiene_2011.csv"),
    "education_access": Path("data/curated/education_access/census_education_access_2011.csv"),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_domain(domain: str, source_header: list[str], inventory: dict) -> dict:
    fields = DOMAIN_FIELDS[domain]
    missing = [f for f in IDENTITY_FIELDS + fields if f not in source_header]
    if missing:
        raise ValueError(f"{domain}: reviewed source fields missing: {missing}")

    observed_candidates = set(inventory["domains"][domain]["candidate_fields"])
    not_observed = [f for f in fields if f not in observed_candidates]
    if not_observed:
        raise ValueError(f"{domain}: reviewed fields absent from observed-schema inventory: {not_observed}")

    # Explicit Water exclusions demonstrate that discovery-token matches are not
    # silently treated as thematic evidence.
    if domain == "water_access":
        forbidden = {"navigable_waterways_river_canal_status_a_1_na_2", "wells_tube_wells_area_in_hectares"}
        if forbidden.intersection(fields):
            raise ValueError("Water reviewed field set includes non-access false-positive schema matches")

    out = OUTPUTS[domain]
    out.parent.mkdir(parents=True, exist_ok=True)
    provenance_fields = [f for f in source_header if f.startswith("source_") or f.startswith("jla_")]
    selected = IDENTITY_FIELDS + fields + [f for f in provenance_fields if f not in IDENTITY_FIELDS + fields]
    blanks = {f: 0 for f in fields}
    row_count = 0
    years: set[str] = set()

    with SOURCE.open("r", encoding="utf-8-sig", newline="") as src, out.open("w", encoding="utf-8", newline="") as dst:
        reader = csv.DictReader(src)
        writer = csv.DictWriter(dst, fieldnames=selected, extrasaction="ignore")
        writer.writeheader()
        for row in reader:
            writer.writerow({f: row.get(f, "") for f in selected})
            row_count += 1
            yr = (row.get("reference_year") or "").strip()
            if yr:
                years.add(yr)
            for f in fields:
                if (row.get(f) or "").strip() == "":
                    blanks[f] += 1

    if row_count < 30_000:
        raise ValueError(f"{domain}: implausibly small source-native village coverage: {row_count}")
    if years != {"2011"}:
        raise ValueError(f"{domain}: unexpected reference years: {sorted(years)}")

    report = {
        "status": "validated_source_native_historical_extract",
        "module": domain,
        "source": str(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "schema_inventory": str(INVENTORY),
        "schema_inventory_source_sha256": inventory["source_sha256"],
        "output": str(out),
        "output_sha256": sha256_file(out),
        "reference_year": 2011,
        "row_count": row_count,
        "thematic_field_count": len(fields),
        "thematic_fields": fields,
        "blank_counts": blanks,
        "geography_rule": "Census 2011 source-native geography only; no current-geography equivalence inferred",
        "missing_rule": "source missing values preserved as empty/null representation; never converted to zero",
        "derivation_rule": "direct reviewed field projection only; no imputation, aggregation, semantic recoding, or current-status inference",
    }
    report_path = out.with_suffix(".provenance.json")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    if not SOURCE.exists() or not INVENTORY.exists():
        raise FileNotFoundError("Governed source or observed-schema inventory is missing")
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    if inventory.get("status") != "observed_schema_inventory_not_publication_approval":
        raise ValueError("Unexpected schema-inventory state")
    if inventory.get("source_sha256") != sha256_file(SOURCE):
        raise ValueError("Schema inventory does not correspond to the current governed source bytes")

    with SOURCE.open("r", encoding="utf-8-sig", newline="") as fh:
        header = next(csv.reader(fh), None)
    if not header:
        raise ValueError("Governed source has no header")

    reports = {domain: build_domain(domain, header, inventory) for domain in DOMAIN_FIELDS}
    print(json.dumps({d: {"rows": r["row_count"], "fields": r["thematic_field_count"]} for d, r in reports.items()}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
