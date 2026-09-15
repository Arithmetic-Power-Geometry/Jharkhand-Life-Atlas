import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "modules" / "health_access" / "evidence" / "hmis_jharkhand_district_catalog_discovery_2026-09-15.json"


def _evidence():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_authoritative_catalog_discovery_does_not_equal_payload_acquisition():
    e = _evidence()
    assert e["evidence_kind"] == "authoritative_catalog_discovery"
    assert e["authority"]["platform"] == "Open Government Data (OGD) Platform India"
    assert e["catalog_api_link_observed"] is True
    assert e["zip_download_label_observed"] is True
    assert e["raw_payload_acquired"] is False
    assert e["raw_sha256"] is None
    assert e["raw_byte_count"] is None
    assert e["schema_inspected"] is False
    assert e["observed_schema"] is None
    assert e["publication_allowed"] is False


def test_catalog_metadata_cannot_bypass_scientific_gates():
    e = _evidence()
    g = e["governance"]
    assert e["geography_linkage_validated"] is False
    assert e["indicator_validation_complete"] is False
    assert g["preserve_missing_as_null"] is True
    assert g["allow_missing_to_zero_conversion"] is False
    assert g["allow_name_only_geography_equivalence"] is False
    assert g["allow_endpoint_synthesis"] is False
    assert g["allow_third_party_payload_substitution"] is False
    assert g["publication_requires_verified_payload_schema_geography_and_indicator_gates"] is True
