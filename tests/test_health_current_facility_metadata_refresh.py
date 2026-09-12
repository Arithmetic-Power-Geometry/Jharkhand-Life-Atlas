from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    ROOT
    / "modules"
    / "health_access"
    / "acquisition_evidence"
    / "2026-09-13_current_facility_metadata_refresh.yaml"
)


def _load():
    return yaml.safe_load(EVIDENCE.read_text(encoding="utf-8"))


def test_current_facility_refresh_is_metadata_only_and_non_publishable():
    evidence = _load()
    assert evidence["module_id"] == "health_access"
    assert evidence["evidence_class"] == "authoritative_metadata_only"
    assert evidence["publication_allowed"] is False
    assert evidence["raw_payload_acquired"] is False
    assert evidence["raw_sha256"] is None
    assert evidence["schema_inspected"] is False
    assert evidence["geography_linkage_established"] is False


def test_advertised_controls_do_not_become_machine_payload_identity():
    evidence = _load()
    observations = evidence["verified_metadata_observations"]
    for resource in observations.values():
        assert resource["machine_resource_id"] is None
        assert resource["direct_payload_url"] is None

    rules = set(evidence["rules"])
    assert "metadata_is_not_payload" in rules
    assert "advertised_download_is_not_acquisition" in rules
    assert "data_api_control_is_not_machine_identity" in rules
    assert "indexed_fields_are_not_payload_schema" in rules
    assert "never_construct_resource_uuid_or_endpoint" in rules
    assert "conflicting_authoritative_surfaces_fail_closed" in rules


def test_refresh_preserves_health_governance_boundaries():
    evidence = _load()
    rules = set(evidence["rules"])
    required = set(evidence["required_next_evidence"])

    assert "missing_values_remain_null" in rules
    assert "no_person_level_health_data" in rules
    assert "no_unsupported_derived_outputs" in rules
    assert "captured authoritative bytes or auditable API response" in required
    assert "retrieval timestamp, final URL, byte count, content type, and SHA-256" in required
    assert "observed payload schema inspection" in required
    assert "explicit Jharkhand filtering at source-native geography" in required
    assert (
        "evidence-backed administrative-vintage linkage before cross-period comparison"
        in required
    )
