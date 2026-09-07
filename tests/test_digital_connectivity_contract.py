from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "digital_connectivity"


def _yaml(name):
    return yaml.safe_load((MODULE / name).read_text(encoding="utf-8"))


def test_module12_is_fail_closed_and_dependency_safe():
    module = _yaml("module.yaml")
    assert module["id"] == "digital_connectivity"
    assert module["status"] == "active"
    assert module["dependencies"] == ["core_geography"]
    assert module["engineering"]["fuzzy_linking"] == "prohibited"
    assert module["engineering"]["missing_numeric_policy"] == "preserve_null_never_zero"
    assert "silently" in module["engineering"]["temporal_geography_policy"].lower()
    assert "snapshot" in module["engineering"]["dynamic_source_policy"].lower()


def test_module12_publication_gate_starts_closed():
    gate = _yaml("completion_gate.yaml")
    assert gate["publication_ready"] is False
    required = {
        "authoritative_acquisition", "rights_review", "geographic_linkage",
        "provenance", "production_schema", "indicators", "validation", "tests",
        "streamlit", "downloads_reports", "documentation", "green_ci_main",
    }
    assert required.issubset(gate["requirements"])
    assert all(gate["requirements"][key]["passed"] is False for key in required)


def test_module12_sources_do_not_claim_unacquired_payloads():
    sources = _yaml("sources.yaml")
    assert sources["status"] == "discovery_active_no_thematic_values_published"
    text = (MODULE / "sources.yaml").read_text(encoding="utf-8").lower()
    assert "not_yet_acquired" in text or "not_yet_selected" in text
    assert "pending" in text


def test_module12_privacy_boundary_blocks_person_level_telecom_records():
    policy = _yaml("module.yaml")["engineering"]["sensitive_data_policy"].lower()
    for forbidden in ["subscriber names", "phone numbers", "device identifiers", "person-level"]:
        assert forbidden in policy
