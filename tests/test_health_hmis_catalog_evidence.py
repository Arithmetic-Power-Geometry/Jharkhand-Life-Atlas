from pathlib import Path

import yaml


EVIDENCE = Path(
    "modules/health_access/acquisition_evidence/"
    "2026-09-12_hmis_quarterly_catalog_controls.yaml"
)


def _load():
    return yaml.safe_load(EVIDENCE.read_text(encoding="utf-8"))


def _is_sha256(value):
    return isinstance(value, str) and len(value) == 64 and all(
        c in "0123456789abcdef" for c in value.lower()
    )


def test_hmis_catalog_blocker_evidence_is_immutable_and_official():
    evidence = _load()
    assert evidence["contract"] == "JLA_HEALTH_OFFICIAL_CATALOG_CONTROL_EVIDENCE_V1"
    assert evidence["source_id"] == "OGD_HMIS_QUARTERLY_FACILITY_EXTREMES_2026"
    assert evidence["catalog_page"]["url"].startswith("https://www.data.gov.in/catalog/")
    assert evidence["control_surface"]["url"].startswith("https://www.data.gov.in/apis/")
    assert evidence["catalog_page"]["http_status"] == 200
    assert evidence["control_surface"]["http_status"] == 200
    assert evidence["catalog_page"]["byte_count"] > 0
    assert evidence["control_surface"]["byte_count"] > 0
    assert _is_sha256(evidence["catalog_page"]["sha256"])
    assert _is_sha256(evidence["control_surface"]["sha256"])
    assert _is_sha256(evidence["workflow"]["artifact"]["sha256"])


def test_hmis_disabled_controls_can_never_be_promoted_to_publishable_data():
    evidence = _load()
    controls = evidence["catalog_page"]["authoritative_controls"]
    result = evidence["result"]

    assert controls["catalog_api"]["present"] is True
    assert controls["catalog_api"]["available"] is False
    assert controls["zip_download"]["present"] is True
    assert controls["zip_download"]["available"] is False
    assert evidence["catalog_page"]["explicit_resource_link_count"] == 0
    assert evidence["catalog_page"]["explicit_resource_uuid_candidates"] == []
    assert result["raw_thematic_payload_acquired"] is False
    assert result["machine_resource_identity_resolved"] is False
    assert result["observed_schema_available"] is False
    assert result["publication_allowed"] is False


def test_hmis_blocker_governance_preserves_non_inference_rules():
    evidence = _load()
    governance = set(evidence["governance"])
    assert "never_construct_child_resource_identity_from_catalog_uuid" in governance
    assert "html_is_not_data" in governance
    assert "preserve_missing_as_null" in governance
    assert "no_name_only_geography_equivalence" in governance
    assert "publication_requires_payload_hash_schema_rights_geography_and_validation_gates" in governance
