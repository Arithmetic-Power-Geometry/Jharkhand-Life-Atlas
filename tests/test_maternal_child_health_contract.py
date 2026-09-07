from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "maternal_child_health" / "module.yaml"
SOURCES = ROOT / "modules" / "maternal_child_health" / "sources.yaml"
GATE = ROOT / "modules" / "maternal_child_health" / "completion_gate.yaml"


def _load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_maternal_child_health_is_active_but_not_complete():
    module = _load(MODULE)
    assert module["id"] == "maternal_child_health"
    assert module["status"] == "active"
    assert module["dependencies"] == ["core_geography"]
    assert "Do not mark complete" in module["completion_gate"]


def test_privacy_missing_geography_and_denominator_safeguards_are_explicit():
    module = _load(MODULE)
    principles = set(module["principles"])
    assert "missing_is_not_zero" in principles
    assert "no_person_level_mother_child_or_contact_identifiers" in principles
    assert "historical_and_current_geographies_not_silently_merged" in principles
    assert module["engineering"]["fuzzy_linking"] == "prohibited"
    assert module["engineering"]["missing_numeric_policy"] == "preserve_null_never_zero"
    sensitive = module["engineering"]["sensitive_data_policy"].lower()
    for forbidden in ["beneficiary", "names", "phone numbers", "person-level"]:
        assert forbidden in sensitive
    assert "do not infer" in module["engineering"]["denominator_policy"].lower()


def test_source_inventory_is_fail_closed_and_person_level_rch_is_excluded():
    sources = _load(SOURCES)["sources"]
    assert sources
    for source in sources:
        assert source["publishable"] is False
        assert source["authority"]
        assert source["url"].startswith("https://")
        assert "rights_status" in source
        assert "acquisition_status" in source
    rch = next(s for s in sources if s["id"] == "RCH_PORTAL_EXCLUDED_PERSON_LEVEL")
    assert "person-level" in rch["exclusion_reason"].lower()


def test_completion_gate_remains_open_until_every_publication_criterion_passes():
    gate = _load(GATE)
    assert gate["module"] == "maternal_child_health"
    assert gate["status"] == "open"
    required = {
        "authoritative_acquisition", "rights_licence_review",
        "smallest_authoritative_reusable_granularity", "cleaning_engineering",
        "geographic_linkage", "provenance", "schema", "indicators",
        "validation", "tests", "streamlit_presentation",
        "downloadable_data_reports", "documentation", "green_ci_on_main",
    }
    assert required.issubset(gate["criteria"])
    assert all(gate["criteria"][key]["satisfied"] is False for key in required)
