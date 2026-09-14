from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "modules" / "health_access" / "completion_gate.yaml"
EXPECTED_SHA256 = "1ddcad9f9b922142a4374c7b89b70fb6cefd8a257448c70a61e1c07d98845134"
IDENTITY_REVIEW = "modules/health_access/evidence/nhd_authoritative_resource_identity_review_2026-09-14.json"
PRIMARY_BINDING = "modules/health_access/evidence/nhd_primary_payload_binding_2026-09-14.json"
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


def test_nhd_gate_is_bound_to_primary_payload_semantic_and_numeric_evidence():
    gate = _gate()
    nhd = gate["verified_partial_evidence"]["national_hospital_directory_candidate_2026_09_13"]
    assert nhd["semantic_contract"] == "modules/health_access/national_hospital_directory_semantic_contract.json"
    assert nhd["numeric_quality_review"] == "modules/health_access/evidence/nhd_numeric_quality_review_2026-09-14.json"
    assert nhd["authoritative_resource_identity_review"] == IDENTITY_REVIEW
    assert nhd["primary_payload_binding"] == PRIMARY_BINDING
    assert nhd["catalog_resource_relationship_verified"] is True
    assert nhd["primary_official_payload_binding_verified"] is True
    assert nhd["candidate_payload_equivalence_to_current_resource_bytes_verified"] is True
    assert nhd["alternate_alias_equivalence_resolved"] is False
    assert nhd["canonical_payload_identity_resolved"] is False
    assert nhd["semantic_field_validation_established"] is False
    assert nhd["systematic_zero_fields_indicator_eligible"] is False
    assert set(nhd["systematic_zero_profile_fields"]) == SYSTEMATIC_ZERO_FIELDS
    rule = nhd["rule"].lower()
    assert "exactly byte-bound" in rule
    assert "alternate official alias remains unresolved" in rule
    assert "canonical alias selection is not permitted" in rule
    assert "not evidence of true absence" in rule
    assert "not indicator-eligible" in rule


def test_nhd_scientific_gates_remain_fail_closed_after_primary_byte_binding():
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


def test_gate_distinguishes_primary_byte_binding_from_canonical_identity():
    gate = _gate()
    acquisition = gate["criteria"]["authoritative_acquisition"]["evidence"].lower()
    provenance = gate["criteria"]["provenance"]["evidence"].lower()
    validation = gate["criteria"]["validation"]["evidence"].lower()
    assert "genuinely acquired" in acquisition
    assert EXPECTED_SHA256 in gate["criteria"]["authoritative_acquisition"]["evidence"]
    assert "explicit primary official payload exactly matches" in acquisition
    assert "alternate official alias returned http 403" in acquisition
    assert "canonical alias selection is prohibited" in acquisition
    assert "unacquired" in acquisition  # reserved for other required sources such as NFHS-5
    assert "exact byte binding" in provenance
    assert "alternate-alias/canonical identity" in provenance
    assert "primary binding cannot be promoted" in validation
    assert "publication permission" in validation


def test_exact_head_ci_must_be_reverified_after_gate_change():
    gate = _gate()
    ci = gate["criteria"]["green_ci_on_main"]
    assert ci["satisfied"] is False
    assert "d8a0ff17659c2c82c6d6471cf385d73872e32058" in ci["evidence"]
    assert "34864917868" in ci["evidence"]
    assert "34864917805" in ci["evidence"]
    assert "re-verified" in ci["evidence"]
