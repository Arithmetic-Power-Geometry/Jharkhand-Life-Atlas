import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "modules" / "health_access" / "evidence" / "nhd_authoritative_resource_identity_review_2026-09-14.json"
PRIMARY_BINDING = ROOT / "modules" / "health_access" / "evidence" / "nhd_primary_payload_binding_2026-09-14.json"
EXPECTED_SHA256 = "1ddcad9f9b922142a4374c7b89b70fb6cefd8a257448c70a61e1c07d98845134"
EXPECTED_BYTES = 10341256


def load_review():
    return json.loads(REVIEW.read_text(encoding="utf-8"))


def load_primary_binding():
    return json.loads(PRIMARY_BINDING.read_text(encoding="utf-8"))


def test_identity_review_is_authoritative_but_fail_closed():
    review = load_review()
    assert review["contract"] == "JLA_HEALTH_NHD_RESOURCE_IDENTITY_REVIEW_V1"
    assert review["publication_allowed"] is False

    metadata = review["authoritative_metadata"]
    assert metadata["host"] == "data.gov.in"
    assert metadata["catalog_resource_relationship_verified"] is True
    assert metadata["metadata_surface_is_authoritative"] is True
    assert metadata["catalog"]["url"].startswith("https://www.data.gov.in/catalog/")
    assert metadata["resource"]["url"].startswith("https://www.data.gov.in/resource/")
    assert metadata["resource"]["parent_catalog_title"] == metadata["catalog"]["title"]

    binding = review["candidate_payload_binding"]
    assert binding["sha256"] == EXPECTED_SHA256
    assert binding["byte_count"] == EXPECTED_BYTES
    assert binding["observed_data_row_count"] == 30273
    assert binding["observed_column_count"] == 48
    assert binding["jharkhand_source_label_row_count"] == 478

    evidence = review["primary_payload_binding_evidence"]
    assert evidence["primary_matches_governed_sha256"] is True
    assert evidence["primary_matches_governed_byte_count"] is True
    assert evidence["primary_exact_payload_binding_verified"] is True
    assert evidence["primary_http_status"] == 200
    assert evidence["alternate_http_status"] == 403
    assert evidence["alternate_alias_equivalence_verified"] is False

    boundary = review["scientific_boundary"]
    assert boundary["primary_authoritative_payload_binding_verified"] is True
    assert boundary["candidate_payload_equivalence_to_all_explicit_current_resource_aliases_verified"] is False
    assert boundary["canonical_payload_identity_resolved"] is False
    assert boundary["record_level_reference_period_verified"] is False
    assert boundary["resource_update_date_may_be_used_as_record_date"] is False
    assert boundary["semantic_field_validation_established"] is False
    assert boundary["systematic_zero_fields_validated_as_true_absence"] is False
    assert boundary["geography_linkage_established"] is False
    assert boundary["source_geography_ids_interpreted"] is False


def test_primary_binding_receipt_is_exact_but_does_not_overclaim_alias_equivalence():
    receipt = load_primary_binding()
    assert receipt["contract"] == "JLA_HEALTH_NHD_PRIMARY_PAYLOAD_BINDING_V1"
    assert receipt["publication_allowed"] is False
    assert receipt["governed_candidate"]["sha256"] == EXPECTED_SHA256
    assert receipt["governed_candidate"]["byte_count"] == EXPECTED_BYTES

    primary = receipt["primary_authoritative_candidate"]
    assert primary["requested_url"].startswith("https://data.gov.in/")
    assert primary["final_url"].startswith("https://www.data.gov.in/")
    assert primary["http_status"] == 200
    assert primary["sha256"] == EXPECTED_SHA256
    assert primary["byte_count"] == EXPECTED_BYTES
    assert primary["matches_governed_candidate_sha256"] is True
    assert primary["matches_governed_candidate_byte_count"] is True
    assert primary["exact_governed_payload_binding_verified"] is True

    alternate = receipt["alternate_authoritative_candidate"]
    assert alternate["http_status"] == 403
    assert alternate["eligible_for_equivalence"] is False
    assert alternate["sha256"] is None
    assert alternate["byte_count"] is None
    assert alternate["equivalence_to_primary_verified"] is False

    boundary = receipt["scientific_boundary"]
    assert boundary["one_explicit_official_payload_candidate_exactly_matches_governed_candidate"] is True
    assert boundary["all_explicit_official_candidates_byte_equivalent"] is False
    assert boundary["canonical_alias_selection_permitted"] is False
    assert boundary["publication_ready"] is False

    privacy = receipt["privacy_and_storage"]
    assert privacy["raw_payload_persisted_in_this_receipt"] is False
    assert privacy["source_rows_persisted_in_this_receipt"] is False
    assert privacy["privacy_risk_values_persisted_in_this_receipt"] is False


def test_identity_review_preserves_missingness_privacy_and_geography_boundaries():
    review = load_review()
    missing = review["missingness_policy"]
    assert missing["source_note_supports_na_blank_as_not_available"] is True
    assert missing["missing_must_remain_null"] is True
    assert missing["missing_must_not_be_converted_to_zero"] is True
    assert missing["observed_zero_must_not_be_reclassified_as_missing_without_authoritative_field_evidence"] is True

    privacy = review["privacy_and_rights_boundary"]
    assert privacy["person_or_contact_fields_authorized_for_publication"] is False
    assert privacy["raw_source_rows_persisted_in_this_receipt"] is False
    assert privacy["privacy_risk_values_persisted_in_this_receipt"] is False

    decision = review["decision"]
    assert decision["catalog_resource_parentage_can_be_treated_as_verified"] is True
    assert decision["primary_official_payload_binding_can_be_treated_as_verified"] is True
    assert decision["alternate_alias_can_be_treated_as_equivalent"] is False
    assert decision["candidate_can_be_treated_as_canonical_publication_payload"] is False
    assert decision["candidate_can_be_used_for_current_latest_indicators"] is False
    assert decision["candidate_can_be_geographically_linked_by_name_only"] is False
    assert decision["publication_gate_remains_closed"] is True

    rules = " ".join(review["rules"]).lower()
    assert "missing remains null" in rules
    assert "names or normalized spellings alone never establish administrative equivalence" in rules
    assert "systematic zeros are not evidence of true absence" in rules
    assert "403" in rules
    assert "partial authoritative retrieval" in rules
