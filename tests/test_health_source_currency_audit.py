from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "modules" / "health_access" / "source_currency_audit_2026-09-11.yaml"


def _audit():
    return yaml.safe_load(AUDIT.read_text(encoding="utf-8"))


def test_current_health_currency_audit_never_claims_payload_acquisition():
    audit = _audit()
    assert audit["audit_scope"] == "current_official_ogd_health_facility_resource_currency"
    assert audit["blocker"] == "exact_authoritative_raw_payload_identity_and_bytes_not_yet_acquired"
    assert len(audit["observations"]) == 2

    for observation in audit["observations"]:
        assert observation["resource_currency_verified"] is True
        assert observation["raw_payload_acquired"] is False
        assert observation["raw_sha256"] is None
        assert observation["schema_inspected"] is False
        assert observation["publication_effect"] == "none_gate_remains_closed"


def test_current_health_currency_audit_preserves_fail_closed_interpretation():
    audit = _audit()
    rules = set(audit["interpretation"])
    required = {
        "live_catalog_currency_is_metadata_not_payload_evidence",
        "advertised_download_or_api_controls_do_not_establish_machine_payload_identity",
        "no_resource_uuid_or_endpoint_may_be_inferred_from_titles_slugs_or_catalog_identifiers",
        "the_two_monthly_resources_must_be_acquired_and_validated_independently",
        "similar_update_dates_do_not_establish_record_equivalence",
        "explicit_jharkhand_filter_and_evidence_backed_geography_validation_are_required_before_curated_use",
        "missing_values_must_remain_null",
        "no_current_facility_inventory_or_access_indicator_may_be_published_from_catalog_metadata",
    }
    assert required.issubset(rules)
