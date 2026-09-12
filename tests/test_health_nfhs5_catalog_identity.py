from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "modules" / "health_access" / "acquisition_evidence" / "2026-09-12_nfhs5_catalog_api_identity.yaml"
RIGHTS = ROOT / "modules" / "health_access" / "RIGHTS_LICENCE_REVIEW.md"


def load_evidence():
    return yaml.safe_load(EVIDENCE.read_text(encoding="utf-8"))


def test_nfhs5_catalog_identity_is_verified_but_not_payload_identity():
    data = load_evidence()
    api = data["catalog_api"]
    assert data["source_id"] == "OGD_NFHS5_DISTRICT_FACTSHEETS_2019_2021"
    assert api["identity_state"] == "verified_from_official_catalog_api_link"
    assert api["catalog_api_id"] == "6f1094bb-24f4-4fe4-8063-cf4cb733279c"
    assert api["official_link_target"].endswith(api["catalog_api_id"])
    assert api["payload_acquired"] is False
    assert data["raw_payload_acquired"] is False
    assert data["raw_sha256"] is None
    assert data["schema_inspected"] is False
    assert data["geography_linkage_established"] is False
    assert data["publication_allowed"] is False


def test_nfhs5_metadata_never_upgrades_to_scientific_evidence():
    data = load_evidence()
    rules = set(data["rules"])
    assert "catalog_api_identity_is_not_resource_payload_identity" in rules
    assert "data_api_button_does_not_establish_resource_uuid" in rules
    assert "never_construct_resource_endpoint_from_catalog_identifier" in rules
    assert "metadata_is_not_payload" in rules
    assert "no_unsupported_derived_outputs" in rules
    assert data["missing_value_rule"].startswith("preserve source missing")
    assert "person-level" in data["privacy_rule"]


def test_nfhs5_official_suppression_semantics_are_fail_closed():
    data = load_evidence()
    resource = data["resource_observation"]
    state = resource["source_metadata_state"]
    suppression = resource["suppression_semantics"]
    rules = set(data["rules"])

    assert state["reference_url_of_resource"] == "observed_as_NA"
    assert state["sourced_webservices_apis"] == "observed_as_NA"
    assert resource["reference_url_of_resource"] is None
    assert resource["sourced_webservices_apis"] is None
    assert "25-49" in suppression["parenthesized_estimate_rule"]
    assert "fewer than 25" in suppression["asterisk_rule"]
    assert "null" in suppression["jla_handling"]
    assert "never convert to zero" in suppression["jla_handling"]
    assert "suppression_is_not_zero" in rules
    assert "suppressed_values_must_not_be_reconstructed" in rules


def test_nfhs5_rights_review_preserves_fail_closed_boundary():
    text = RIGHTS.read_text(encoding="utf-8")
    assert "NFHS-5 district factsheet" in text
    assert "Government Open Data License - India" in text
    assert "catalog/API identity does not authorize publication" in text
    assert "raw workbook bytes" in text
    assert "suppression" in text
