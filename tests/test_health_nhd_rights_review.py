import json
from pathlib import Path


REVIEW_PATH = Path(
    "modules/health_access/evidence/nhd_rights_review_2026-09-14.json"
)


def _review() -> dict:
    return json.loads(REVIEW_PATH.read_text(encoding="utf-8"))


def test_rights_review_is_fail_closed():
    review = _review()
    assert review["contract"] == "JLA_HEALTH_NHD_RIGHTS_REVIEW_V1"
    assert review["status"] == "reviewed_with_exclusions_and_remaining_gates"
    assert review["publication_allowed"] is False
    assert review["rights_decision"]["rights_review_alone_authorizes_publication"] is False


def test_ogdl_personal_information_exclusion_is_enforced():
    review = _review()
    license_info = review["license"]
    decision = review["rights_decision"]
    assert license_info["permits_lawful_reuse_adaptation_and_publication"] is True
    assert license_info["attribution_required"] is True
    assert license_info["personal_information_excluded_from_license"] is True
    assert decision["personal_or_named_contact_fields_must_not_be_published_from_this_candidate"] is True
    assert decision["public_projection_must_pass_repository_privacy_gate"] is True


def test_rights_review_is_bound_to_verified_candidate_without_rows():
    review = _review()
    payload = review["payload_binding"]
    assert payload["candidate_sha256"] == "1ddcad9f9b922142a4374c7b89b70fb6cefd8a257448c70a61e1c07d98845134"
    assert payload["candidate_byte_count"] == 10341256
    assert payload["observed_data_row_count"] == 30273
    assert payload["observed_column_count"] == 48
    assert payload["privacy_risk_column_count"] == 13
    assert payload["privacy_risk_values_reviewed_or_exported"] is False
    assert payload["raw_snapshot_exported"] is False


def test_rights_gate_does_not_bypass_scientific_and_geography_gates():
    review = _review()
    gates = review["remaining_publication_gates"]
    assert any("canonical resource identity" in gate for gate in gates)
    assert any("privacy-risk" in gate for gate in gates)
    assert any("geographic identifiers" in gate for gate in gates)
    assert any("temporal/reference-period" in gate for gate in gates)
    assert any("scientific validation" in gate for gate in gates)
    assert any("main-head CI" in gate for gate in gates)
