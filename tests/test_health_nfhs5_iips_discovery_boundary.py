from pathlib import Path

import yaml


AUDIT = Path("modules/health_access/evidence/nfhs5_iips_discovery_audit_2026-09-12.yaml")
GATE = Path("modules/health_access/completion_gate.yaml")


def test_iips_nfhs5_discovery_is_authoritative_but_not_payload_evidence():
    audit = yaml.safe_load(AUDIT.read_text(encoding="utf-8"))

    assert audit["audit_contract"] == "JLA_AUTHORITATIVE_DISCOVERY_AUDIT_V1"
    assert audit["module_id"] == "health_access"
    assert audit["authority"]["organization"] == "International Institute for Population Sciences (IIPS)"
    assert audit["authority"]["official_landing_url"].startswith("https://www.iipsindia.ac.in/")
    assert audit["retrieval_result"]["landing_page_verified"] is True

    result = audit["retrieval_result"]
    assert result["delegated_page_payload_acquired"] is False
    assert result["raw_payload_acquired"] is False
    assert result["raw_sha256"] is None
    assert result["raw_bytes"] is None
    assert result["schema_inspected"] is False
    assert result["jharkhand_rows_extracted"] is False
    assert result["publication_allowed"] is False


def test_iips_discovery_cannot_close_health_publication_gate():
    gate = yaml.safe_load(GATE.read_text(encoding="utf-8"))

    assert gate["status"] == "open"
    for criterion in (
        "authoritative_acquisition",
        "smallest_authoritative_reusable_granularity",
        "cleaning_engineering",
        "geographic_linkage",
        "provenance",
        "indicators",
        "validation",
        "downloadable_data_reports",
    ):
        assert gate["criteria"][criterion]["satisfied"] is False


def test_iips_discovery_rules_preserve_missingness_and_forbid_inferred_identity():
    audit = yaml.safe_load(AUDIT.read_text(encoding="utf-8"))
    rules = " ".join(audit["boundary_rules"]).lower()

    assert "must remain null" in rules
    assert "never convert them to zero" in rules
    assert "do not infer or construct" in rules
    assert "geographically validated" in rules
