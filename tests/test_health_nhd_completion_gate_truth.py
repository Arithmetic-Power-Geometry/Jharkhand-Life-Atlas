from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "modules" / "health_access" / "completion_gate.yaml"
EXPECTED_SHA256 = "1ddcad9f9b922142a4374c7b89b70fb6cefd8a257448c70a61e1c07d98845134"
SYSTEMATIC_ZERO_FIELDS = {
    "Establised_Year",
    "Number_Doctor",
    "Num_Mediconsultant_or_Expert",
    "Total_Num_Beds",
    "Number_Private_Wards",
    "Num_Bed_for_Eco_Weaker_Sec",
}


def _gate():
    return yaml.safe_load(GATE.read_text(encoding="utf-8"))


def test_nhd_candidate_is_recorded_as_acquired_but_nonpublishing():
    gate = _gate()
    nhd = gate["verified_partial_evidence"]["national_hospital_directory_candidate_2026_09_13"]
    assert nhd["source_sha256"] == EXPECTED_SHA256
    assert nhd["source_byte_count"] == 10_341_256
    assert nhd["observed_data_row_count"] == 30_273
    assert nhd["observed_column_count"] == 48
    assert nhd["jharkhand_source_label_row_count"] == 478
    assert nhd["raw_payload_acquired_and_hashed_in_ephemeral_ci"] is True
    assert nhd["raw_payload_redistributed"] is False
    assert nhd["schema_inspected"] is True
    assert nhd["curated_dataset_emitted"] is False
    assert nhd["publication_allowed"] is False


def test_nhd_gate_is_bound_to_semantic_and_numeric_quality_evidence():
    gate = _gate()
    nhd = gate["verified_partial_evidence"]["national_hospital_directory_candidate_2026_09_13"]
    assert nhd["semantic_contract"] == "modules/health_access/national_hospital_directory_semantic_contract.json"
    assert nhd["numeric_quality_review"] == "modules/health_access/evidence/nhd_numeric_quality_review_2026-09-14.json"
    assert nhd["semantic_field_validation_established"] is False
    assert nhd["systematic_zero_fields_indicator_eligible"] is False
    assert set(nhd["systematic_zero_profile_fields"]) == SYSTEMATIC_ZERO_FIELDS
    rule = nhd["rule"].lower()
    assert "not evidence of true absence" in rule
    assert "not indicator-eligible" in rule


def test_nhd_scientific_gates_remain_fail_closed():
    gate = _gate()
    nhd = gate["verified_partial_evidence"]["national_hospital_directory_candidate_2026_09_13"]
    assert nhd["geography_linkage_established"] is False
    assert nhd["record_level_reference_period_verified"] is False
    criteria = gate["criteria"]
    assert criteria["authoritative_acquisition"]["satisfied"] is False
    assert criteria["cleaning_engineering"]["satisfied"] is False
    assert criteria["geographic_linkage"]["satisfied"] is False
    assert criteria["provenance"]["satisfied"] is False
    assert criteria["indicators"]["satisfied"] is False
    assert criteria["validation"]["satisfied"] is False
    assert criteria["downloadable_data_reports"]["satisfied"] is False
    indicator_evidence = criteria["indicators"]["evidence"]
    for field in SYSTEMATIC_ZERO_FIELDS:
        assert field in indicator_evidence
    assert "not indicator-eligible" in indicator_evidence


def test_gate_no_longer_claims_current_facility_payload_is_unacquired():
    gate = _gate()
    acquisition = gate["criteria"]["authoritative_acquisition"]["evidence"].lower()
    assert "genuinely acquired" in acquisition
    assert EXPECTED_SHA256 in gate["criteria"]["authoritative_acquisition"]["evidence"]
    assert "non-canonical" in acquisition
    assert "unacquired" in acquisition  # reserved for other required sources such as NFHS-5
    assert "nhd" not in acquisition.split("unacquired")[0][-40:]  # never describe NHD itself as unacquired


def test_exact_head_ci_must_be_reverified_after_gate_change():
    gate = _gate()
    ci = gate["criteria"]["green_ci_on_main"]
    assert ci["satisfied"] is False
    assert "5ebb1fbd716e87b672c1b5210f8f6b650e43ea88" in ci["evidence"]
    assert "34819571684" in ci["evidence"]
    assert "34819571681" in ci["evidence"]
    assert "re-verified" in ci["evidence"]
