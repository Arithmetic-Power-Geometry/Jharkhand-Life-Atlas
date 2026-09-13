import json
from pathlib import Path


RECEIPT_PATH = Path(
    "modules/health_access/evidence/nhd_jharkhand_aggregate_receipt_2026-09-13.json"
)


def _receipt() -> dict:
    return json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))


def test_persisted_health_evidence_is_fail_closed():
    receipt = _receipt()

    assert receipt["contract"] == "JLA_HEALTH_NHD_PERSISTED_AGGREGATE_EVIDENCE_V1"
    assert receipt["status"] == "candidate_evidence_only"
    assert receipt["publication_allowed"] is False
    assert receipt["curated_dataset_emitted"] is False
    assert receipt["geography_linkage_status"] == "unresolved"
    assert receipt["source"]["canonical_source_identity_resolved"] is False


def test_persisted_health_evidence_binds_verified_source_and_ci():
    receipt = _receipt()
    source = receipt["source"]
    ci = receipt["ci_provenance"]

    assert source["sha256"] == "1ddcad9f9b922142a4374c7b89b70fb6cefd8a257448c70a61e1c07d98845134"
    assert source["byte_count"] == 10341256
    assert source["observed_data_row_count"] == 30273
    assert source["observed_column_count"] == 48
    assert source["observed_row_width_mismatch_count"] == 0
    assert ci["head_sha"] == "38f7d106ce0cc6e24f404c7b861e00bd6b8ad984"
    assert ci["conclusion"] == "success"
    assert ci["artifact_digest"].startswith("sha256:")


def test_persisted_health_evidence_preserves_aggregate_only_boundary():
    receipt = _receipt()
    privacy = receipt["privacy"]
    audit = receipt["jharkhand_aggregate_audit"]

    assert privacy["source_rows_emitted"] is False
    assert privacy["privacy_risk_values_emitted"] is False
    assert privacy["raw_snapshot_exported_as_artifact"] is False
    assert privacy["candidate_public_projection_authorizes_publication"] is False
    assert audit["row_count"] == 478
    assert audit["establishes_administrative_equivalence"] is False
    assert audit["district_identifier_audit"]["internally_one_to_one"] is False
    assert audit["district_identifier_audit"]["administrative_equivalence_established"] is False
    assert audit["state_identifier_audit"]["internally_one_to_one"] is False
    assert audit["state_identifier_audit"]["administrative_equivalence_established"] is False


def test_persisted_health_missingness_is_explicit_not_zero_filled():
    receipt = _receipt()
    audit = receipt["jharkhand_aggregate_audit"]
    null_counts = audit["candidate_projection_null_counts"]

    assert "no zero filling performed" in audit["null_policy"]
    assert null_counts["Specialties"] == 2
    assert null_counts["Number_Doctor"] == 3
    assert null_counts["Total_Num_Beds"] == 0
    assert null_counts["District"] == 0


def test_label_normalization_remains_diagnostic_only():
    receipt = _receipt()
    audit = receipt["jharkhand_aggregate_audit"]

    assert audit["raw_distinct_district_label_count"] == 25
    assert audit["normalized_distinct_district_label_count"] == 24
    assert audit["district_label_normalization_collision_count"] == 1
    assert audit["district_label_normalization_collisions"] == {
        "khunti": ["Khunti", "khunti"]
    }
