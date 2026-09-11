from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "modules" / "health_access" / "acquisition_attempts.yaml"


def _attempts():
    payload = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    return payload["attempts"], payload["rules"]


def test_failed_or_unresolved_health_acquisitions_never_claim_payload_evidence():
    attempts, _ = _attempts()
    assert attempts

    for attempt in attempts:
        result = str(attempt.get("acquisition_result", "")).lower()
        unresolved = (
            "no_payload" in result
            or "unresolved" in result
            or "not_acquired" in result
            or "request_failed" in result
            or attempt.get("raw_payload_acquired") is False
        )
        if not unresolved:
            continue

        assert attempt.get("raw_sha256") is None
        assert attempt.get("raw_bytes") is None
        assert attempt.get("schema_inspected") is False
        assert attempt.get("publication_effect") == "none_gate_remains_closed"


def test_health_acquisition_ledger_preserves_fail_closed_scientific_rules():
    _, rules = _attempts()
    required = {
        "catalog_metadata_is_not_raw_data",
        "resource_page_metadata_is_not_raw_data",
        "failed_requests_do_not_satisfy_acquisition",
        "hashes_and_byte_counts_exist_only_after_real_payload_acquisition",
        "exact_resource_or_api_identifiers_are_never_inferred_from_titles_or_search_snippets",
        "never_create_placeholder_payloads",
        "missing_values_are_never_imputed_as_zero",
    }
    assert required.issubset(set(rules))
