#!/usr/bin/env python3
"""Build the source-native Census 2011 Health & Healthcare Access extract.

This builder reuses only the already-governed Module 1 PTCA village-amenities
output. It performs no current-geography remapping, no imputation, no missing-
to-zero conversion, and no semantic recoding of source fields. The result is
therefore a historical 2011 source-native evidence table, not a claim about
current facility availability.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

SOURCE = Path("data/curated/core_geography/village_amenities_2011.csv")
OUTPUT = Path("data/curated/health_access/census_health_access_2011.csv")
REPORT = Path("data/curated/health_access/census_health_access_2011.provenance.json")

IDENTITY_FIELDS = [
    "state_code", "state_name", "district_code", "district_name",
    "sub_district_code", "sub_district_name", "village_code", "village_name",
    "cd_block_code", "cd_block_name", "gram_panchayat_code",
    "gram_panchayat_name", "reference_year",
]

# Exact source-native PTCA fields verified in the governed Module 1 schema.
# Historical spelling in the Census-derived header is deliberately preserved.
HEALTH_FIELDS = [
    "community_health_centre_numbers",
    "community_health_centre_doctors_total_strength_numbers",
    "community_health_centre_doctors_in_position_numbers",
    "community_health_centre_para_medical_staff_total_strength_numbers",
    "community_health_centre_para_medical_staff_in_position_numbers",
    "if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_15",
    "primary_health_centre_numbers",
    "primary_health_centre_doctors_total_strength_numbers",
    "primary_health_centre_doctors_in_position_numbers",
    "primary_health_centre_para_medical_staff_total_strength_numbers",
    "primary_health_centre_para_medical_staff_in_position_numbers",
    "if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_16",
    "primary_heallth_sub_centre_numbers",
    "primary_heallth_sub_centre_doctors_total_strength_numbers",
    "primary_heallth_sub_centre_doctors_in_position_numbers",
    "primary_heallth_sub_centre_para_medical_staff_total_strength_numbers",
    "primary_heallth_sub_centre_para_medical_staff_in_position_numbers",
    "if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_17",
    "maternity_and_child_welfare_centre_numbers",
    "maternity_and_child_welfare_centre_doctors_total_strength_numbers",
    "maternity_and_child_welfare_centre_doctors_in_position_numbers",
    "maternity_and_child_welfare_centre_para_medical_staff_total_strength_numbers",
    "maternity_and_child_welfare_centre_para_medical_staff_in_position_numbers",
    "if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_18",
    "tb_clinic_numbers",
    "tb_clinic_doctors_total_strength_numbers",
    "tb_clinic_doctors_in_position_numbers",
    "tb_clinic_para_medical_para_medical_staff_total_strength_numbers",
    "tb_clinic_para_medical_para_medical_staff_in_position_numbers",
    "if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_19",
    "hospital_allopathic_numbers",
    "hospital_allopathic_doctors_total_strength_numbers",
    "hospital_allopathic_doctors_in_position_numbers",
    "hospital_allopathic_para_medical_staff_total_strength_numbers",
    "hospital_allopathic_para_medical_staff_in_position_numbers",
    "if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_20",
    "hospiltal_alternative_medicine_numbers",
    "hospiltal_alternative_medicine_doctors_total_strength_numbers",
    "hospiltal_alternative_medicine_doctors_in_position_numbers",
    "hospiltal_alternative_medicine_para_medical_staff_total_strength_numbers",
    "hospiltal_alternative_medicine_para_medical_staff_in_position_numbers",
    "if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_21",
    "dispensary_numbers",
    "dispensary_doctors_total_strength_numbers",
    "dispensary_doctors_in_position_numbers",
    "dispensary_para_medical_staff_total_strength_numbers",
    "dispensary_para_medical_staff_in_position_numbers",
    "if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_22",
    "mobile_health_clinic_numbers",
    "mobile_health_clinic_doctors_total_strength_numbers",
    "mobile_health_clinic_doctors_in_position_numbers",
    "mobile_health_clinic_para_medical_staff_total_strength_numbers",
    "mobile_health_clinic_para_medical_staff_in_position_numbers",
    "if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_24",
    "family_welfare_centre_numbers",
    "family_welfare_centre_doctors_total_strength_numbers",
    "family_welfare_centre_doctors_in_position_numbers",
    "family_welfare_centre_para_medical_staff_total_strength_numbers",
    "family_welfare_centre_para_medical_staff_in_position_numbers",
    "if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_25",
    "non_government_medical_facilities_out_patient_numbers",
    "non_government_medical_facilities_in_and_out_patient_numbers",
    "non_government_medical_facilities_charitable_numbers",
    "non_government_medical_facilities_medical_prctitioner_with_mbbs_degree_numbers",
    "non_government_medical_facilities_medical_prctitioner_with_other_degree_numbers",
    "non_government_medical_facilities_medical_practitioner_with_no_degree_numbers",
    "non_government_medical_facilities_traditional_practitioner_and_faith_healer_numbers",
    "non_government_medical_facilities_medicine_shop_numbers",
    "non_government_medical_facilities_others_numbers",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build() -> dict:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    row_count = 0
    blank_counts: dict[str, int] = {}
    observed_years: set[str] = set()

    with SOURCE.open("r", encoding="utf-8-sig", newline="") as src:
        reader = csv.DictReader(src)
        header = reader.fieldnames or []
        missing_required = [f for f in IDENTITY_FIELDS + HEALTH_FIELDS if f not in header]
        if missing_required:
            raise ValueError(f"Required governed source fields missing: {missing_required}")

        provenance_fields = [
            f for f in header
            if f.startswith("source_") or f.startswith("jla_")
        ]
        selected = IDENTITY_FIELDS + HEALTH_FIELDS + [
            f for f in provenance_fields if f not in IDENTITY_FIELDS + HEALTH_FIELDS
        ]
        blank_counts = {f: 0 for f in HEALTH_FIELDS}

        with OUTPUT.open("w", encoding="utf-8", newline="") as dst:
            writer = csv.DictWriter(dst, fieldnames=selected, extrasaction="ignore")
            writer.writeheader()
            for row in reader:
                # No parsing/coercion: values are copied source-native. Empty stays empty.
                writer.writerow({f: row.get(f, "") for f in selected})
                row_count += 1
                yr = (row.get("reference_year") or "").strip()
                if yr:
                    observed_years.add(yr)
                for f in HEALTH_FIELDS:
                    if (row.get(f) or "").strip() == "":
                        blank_counts[f] += 1

    if row_count == 0:
        raise ValueError("Source amenities table contains no records")
    if observed_years != {"2011"}:
        raise ValueError(f"Unexpected reference years in historical extract: {sorted(observed_years)}")

    report = {
        "status": "validated_source_native_historical_extract",
        "module": "health_access",
        "source": str(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "output": str(OUTPUT),
        "output_sha256": sha256_file(OUTPUT),
        "reference_year": 2011,
        "row_count": row_count,
        "health_field_count": len(HEALTH_FIELDS),
        "blank_counts": blank_counts,
        "geography_rule": "Census 2011 source-native geography only; no current-geography equivalence inferred",
        "missing_rule": "source missing values preserved as empty/null representation; never converted to zero",
        "derivation_rule": "direct field projection only; no imputation, aggregation, recoding, or derived availability claims",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
