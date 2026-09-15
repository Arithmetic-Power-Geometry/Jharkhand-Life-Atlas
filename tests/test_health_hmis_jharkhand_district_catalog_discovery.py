import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "modules" / "health_access" / "evidence" / "hmis_jharkhand_district_catalog_discovery_2026-09-15.json"


def _evidence():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_authoritative_resource_discovery_does_not_equal_payload_acquisition():
    e = _evidence()
    assert e["contract"] == "JLA_HEALTH_HMIS_JHARKHAND_DISTRICT_CATALOG_DISCOVERY_V3"
    assert e["evidence_kind"] == "authoritative_catalog_and_resource_discovery"
    assert e["authority"]["platform"] == "Open Government Data (OGD) Platform India"
    assert e["catalog_api_link_observed"] is True
    assert e["zip_download_label_observed"] is True
    assert e["explicit_authoritative_resource_discovered"] is True
    r = e["resource"]
    assert r["format_label"] == "CSV"
    assert r["granularity"] == "Monthly"
    assert r["provisional"] is True
    assert r["reference_period_text"] == "2014-2015 and Month - upto December"
    assert r["api_exists"] is False
    assert e["raw_payload_acquired"] is False
    assert e["raw_sha256"] is None
    assert e["raw_byte_count"] is None
    assert e["schema_inspected"] is False
    assert e["observed_schema"] is None
    assert e["publication_allowed"] is False


def test_resource_metadata_cannot_bypass_scientific_gates():
    e = _evidence()
    r = e["resource"]
    g = e["governance"]
    assert r["declared_fields_are_observed_schema"] is False
    assert e["geography_linkage_validated"] is False
    assert e["indicator_validation_complete"] is False
    assert g["preserve_missing_as_null"] is True
    assert g["allow_missing_to_zero_conversion"] is False
    assert g["allow_name_only_geography_equivalence"] is False
    assert g["allow_endpoint_synthesis"] is False
    assert g["allow_third_party_payload_substitution"] is False
    assert g["allow_declared_fields_as_observed_schema"] is False
    assert g["allow_provisional_period_as_current_conditions"] is False
    assert g["publication_requires_verified_payload_schema_geography_and_indicator_gates"] is True


def test_resource_recovery_does_not_promote_payload_status():
    e = _evidence()
    retry = e["authoritative_resource_retry"]
    assert retry["result"] == "authoritative_resource_page_retrievable_via_independent_web_verification"
    assert retry["resource_metadata_reverified"] is True
    assert retry["payload_bytes_obtained"] is False
    assert retry["endpoint_inferred"] is False
    assert retry["third_party_payload_used"] is False
    assert e["raw_payload_acquired"] is False
    assert e["publication_allowed"] is False
