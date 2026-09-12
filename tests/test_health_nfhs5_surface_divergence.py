from pathlib import Path

import yaml


EVIDENCE = Path(
    "modules/health_access/acquisition_evidence/"
    "2026-09-12_nfhs5_live_index_surface_divergence.yaml"
)


def _evidence():
    return yaml.safe_load(EVIDENCE.read_text(encoding="utf-8"))


def test_nfhs5_surface_divergence_is_fail_closed():
    evidence = _evidence()
    assert evidence["module_id"] == "health_access"
    assert evidence["observation"]["live_catalog_surface"]["resource_listing_text"] == "No Result Found"
    assert evidence["observation"]["indexed_catalog_record"]["advertised_format"] == "XLS"
    assert evidence["interpretation"]["state"] == "authoritative_surface_divergence_fail_closed"
    assert evidence["publication_allowed"] is False
    assert evidence["raw_payload_acquired"] is False
    assert evidence["raw_sha256"] is None
    assert evidence["schema_inspected"] is False
    assert evidence["geography_linkage_established"] is False


def test_nfhs5_surface_divergence_cannot_be_used_to_infer_payload_identity():
    evidence = _evidence()
    rules = " ".join(evidence["rules"]).lower()
    interpretation = evidence["interpretation"]["rule"].lower()

    assert "indexed_metadata_is_not_payload" in rules
    assert "never_construct_resource_endpoint_from_catalog_metadata" in rules
    assert "no_publication_without_exact_bytes_and_hash" in rules
    assert "must not synthesize a resource uuid" in interpretation
    assert "exact authoritative workbook bytes" in interpretation


def test_nfhs5_surface_divergence_preserves_missingness():
    evidence = _evidence()
    missing_rule = evidence["missing_value_rule"].lower()
    assert "null" in missing_rule
    assert "never convert missing to zero" in missing_rule
