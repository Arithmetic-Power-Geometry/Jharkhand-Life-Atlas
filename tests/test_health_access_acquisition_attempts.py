from pathlib import Path

import yaml


def test_health_acquisition_attempts_are_fail_closed():
    data = yaml.safe_load(Path("modules/health_access/acquisition_attempts.yaml").read_text(encoding="utf-8"))
    assert data["module_id"] == "health_access"
    assert data["attempts"]
    for attempt in data["attempts"]:
        assert attempt["acquisition_result"] != "payload_acquired"
        assert attempt["raw_sha256"] is None
        assert attempt["raw_bytes"] is None
        assert attempt["schema_inspected"] is False
        assert attempt["publication_effect"] == "none_gate_remains_closed"


def test_health_acquisition_rules_reject_placeholder_evidence():
    data = yaml.safe_load(Path("modules/health_access/acquisition_attempts.yaml").read_text(encoding="utf-8"))
    rules = set(data["rules"])
    assert "catalog_metadata_is_not_raw_data" in rules
    assert "failed_requests_do_not_satisfy_acquisition" in rules
    assert "never_create_placeholder_payloads" in rules
    assert "missing_values_are_never_imputed_as_zero" in rules


def test_national_hmis_candidate_cannot_silently_replace_jharkhand_series():
    data = yaml.safe_load(Path("modules/health_access/acquisition_attempts.yaml").read_text(encoding="utf-8"))
    rules = set(data["rules"])
    assert "newer_national_catalog_does_not_silently_replace_jharkhand_specific_series" in rules
    assert "national_payload_requires_explicit_jharkhand_filter_before_curated_use" in rules
    assert "district_aggregates_are_never_allocated_to_villages_or_facilities" in rules

    candidate = next(a for a in data["attempts"] if a["source_id"] == "OGD_HMIS_ALL_STATES_DISTRICTS_2025")
    assert candidate["relationship_to_jharkhand_specific_catalog"] == "parallel_newer_candidate_not_substitute"
    required = set(candidate["required_before_use"])
    assert "explicitly_filter_jharkhand" in required
    assert "verify_district_geography_vintage" in required
    assert "compare_overlap_with_jharkhand_specific_catalog" in required
    assert candidate["acquisition_result"] != "payload_acquired"
