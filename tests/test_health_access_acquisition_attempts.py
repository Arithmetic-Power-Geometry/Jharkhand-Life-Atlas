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
