import csv
import json
from pathlib import Path

from modules.health_access.audit_nhd_candidate_rows import audit_rows


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    observed_columns = [
        "Hospital_Name", "State", "District", "Number_Doctor", "Total_Num_Beds",
        "Telephone", "Nodal_Person_Info", "State_ID", "District_ID",
    ]
    contract = {
        "contract": "TEST_NHD_SCHEMA_V1",
        "source_sha256": "a" * 64,
        "observed_columns": observed_columns,
        "observed_data_row_count": 5,
        "candidate_public_projection": [
            "Hospital_Name", "State", "District", "Number_Doctor", "Total_Num_Beds",
            "State_ID", "District_ID",
        ],
        "privacy_risk_columns": ["Telephone", "Nodal_Person_Info"],
        "publication_allowed": False,
        "geography_linkage_status": "unresolved",
    }
    contract_path = tmp_path / "contract.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    semantic_contract = {
        "contract": "JLA_HEALTH_NHD_SEMANTIC_CONTRACT_V2",
        "publication_allowed": False,
        "row_level_curated_dataset_emitted": False,
        "null_policy": {
            "source_missing_tokens": ["", "NA", "N/A", "Blank"],
            "canonical_missing_representation": None,
            "missing_to_zero_allowed": False,
        },
        "field_groups": {
            "numeric_candidate_fields": ["Number_Doctor", "Total_Num_Beds"],
        },
        "numeric_cleaning_rules": {
            "parse_only_when_unambiguous": True,
            "negative_counts_allowed": False,
            "failed_parse_becomes_null": True,
            "zero_is_observed_value_only": True,
            "no_imputation": True,
        },
    }
    semantic_path = tmp_path / "semantic_contract.json"
    semantic_path.write_text(json.dumps(semantic_contract), encoding="utf-8")

    csv_path = tmp_path / "candidate.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=observed_columns)
        writer.writeheader()
        writer.writerow({
            "Hospital_Name": "A", "State": "Jharkhand", "District": "Ranchi",
            "Number_Doctor": "10", "Total_Num_Beds": "50", "Telephone": "111",
            "Nodal_Person_Info": "Person A", "State_ID": "20", "District_ID": "101",
        })
        writer.writerow({
            "Hospital_Name": "B", "State": "Jharkhand", "District": "Ranchi",
            "Number_Doctor": "NA", "Total_Num_Beds": "0", "Telephone": "222",
            "Nodal_Person_Info": "Person B", "State_ID": "20", "District_ID": "102",
        })
        writer.writerow({
            "Hospital_Name": "C", "State": " jharkhand ", "District": "Khunti",
            "Number_Doctor": "N/A", "Total_Num_Beds": "12.5", "Telephone": "333",
            "Nodal_Person_Info": "Person C", "State_ID": "20", "District_ID": "102",
        })
        writer.writerow({
            "Hospital_Name": "C2", "State": "Jharkhand", "District": "khunti",
            "Number_Doctor": "Blank", "Total_Num_Beds": "-2", "Telephone": "334",
            "Nodal_Person_Info": "Person C2", "State_ID": "20", "District_ID": "102",
        })
        writer.writerow({
            "Hospital_Name": "D", "State": "Bihar", "District": "Patna",
            "Number_Doctor": "5", "Total_Num_Beds": "20", "Telephone": "444",
            "Nodal_Person_Info": "Person D", "State_ID": "10", "District_ID": "201",
        })
    return csv_path, contract_path, semantic_path


def test_audit_is_aggregate_only_and_honors_governed_missing_tokens(tmp_path):
    csv_path, contract_path, semantic_path = _write_fixture(tmp_path)
    report = audit_rows(csv_path, contract_path, semantic_path)

    assert report["contract"] == "JLA_HEALTH_NHD_AGGREGATE_ROW_AUDIT_V3"
    assert report["semantic_contract"] == "JLA_HEALTH_NHD_SEMANTIC_CONTRACT_V2"
    assert report["source_row_count_verified"] == 5
    assert report["jharkhand_source_label_match"]["row_count"] == 4
    assert report["jharkhand_source_label_match"]["establishes_administrative_equivalence"] is False
    assert report["candidate_projection_null_counts"]["Number_Doctor"] == 3
    assert report["candidate_projection_null_counts"]["Total_Num_Beds"] == 0
    assert report["source_missing_tokens"] == ["", "NA", "N/A", "Blank"]
    assert report["canonical_missing_representation"] is None
    assert report["missing_to_zero_allowed"] is False
    assert report["zero_is_observed_value_only"] is True
    assert report["source_rows_emitted"] is False
    assert report["privacy_risk_columns_read_for_output"] == []
    assert report["publication_allowed"] is False


def test_audit_numeric_quality_is_aggregate_and_fail_closed(tmp_path):
    csv_path, contract_path, semantic_path = _write_fixture(tmp_path)
    report = audit_rows(csv_path, contract_path, semantic_path)

    doctors = report["numeric_candidate_quality"]["Number_Doctor"]
    assert doctors["missing_count"] == 3
    assert doctors["observed_nonmissing_count"] == 1
    assert doctors["parseable_nonnegative_integer_count"] == 1
    assert doctors["zero_count"] == 0
    assert doctors["negative_count"] == 0
    assert doctors["noninteger_numeric_count"] == 0
    assert doctors["unparsable_count"] == 0
    assert doctors["raw_values_emitted"] is False

    beds = report["numeric_candidate_quality"]["Total_Num_Beds"]
    assert beds["missing_count"] == 0
    assert beds["observed_nonmissing_count"] == 4
    assert beds["parseable_nonnegative_integer_count"] == 2
    assert beds["zero_count"] == 1
    assert beds["negative_count"] == 1
    assert beds["noninteger_numeric_count"] == 1
    assert beds["unparsable_count"] == 0
    assert beds["raw_values_emitted"] is False


def test_audit_detects_source_identifier_ambiguity(tmp_path):
    csv_path, contract_path, semantic_path = _write_fixture(tmp_path)
    report = audit_rows(csv_path, contract_path, semantic_path)

    district = report["district_identifier_audit"]
    assert district["labels_with_multiple_ids_count"] == 1
    assert district["ids_with_multiple_labels_count"] == 1
    assert district["internally_one_to_one"] is False
    assert district["administrative_equivalence_established"] is False


def test_audit_separates_casefold_collision_from_admin_equivalence(tmp_path):
    csv_path, contract_path, semantic_path = _write_fixture(tmp_path)
    report = audit_rows(csv_path, contract_path, semantic_path)

    normalized = report["district_label_normalization_audit"]
    assert normalized["raw_distinct_label_count"] == 3
    assert normalized["normalized_distinct_label_count"] == 2
    assert normalized["normalization_collision_count"] == 1
    assert normalized["normalization_collisions"] == {"khunti": ["Khunti", "khunti"]}
    assert normalized["administrative_equivalence_established"] is False


def test_audit_never_emits_privacy_values_or_rejected_numeric_values(tmp_path):
    csv_path, contract_path, semantic_path = _write_fixture(tmp_path)
    report_text = json.dumps(audit_rows(csv_path, contract_path, semantic_path))

    assert "Person A" not in report_text
    assert "Person B" not in report_text
    assert '"111"' not in report_text
    assert '"222"' not in report_text
    assert '"12.5"' not in report_text
    assert '"-2"' not in report_text
