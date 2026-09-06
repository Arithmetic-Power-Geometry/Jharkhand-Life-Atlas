from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "education_access" / "module.yaml"
SOURCES = ROOT / "modules" / "education_access" / "sources.yaml"


def _load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_education_module_is_active_not_complete_before_publication_gate():
    module = _load(MODULE)
    assert module["id"] == "education_access"
    assert module["status"] == "active"
    assert module["dependencies"] == ["core_geography"]
    assert "Do not mark complete" in module["completion_gate"]


def test_education_privacy_temporal_and_missing_value_safeguards_are_explicit():
    module = _load(MODULE)
    principles = set(module["principles"])
    assert "missing_is_not_zero" in principles
    assert "no_student_person_level_or_contact_identifiers" in principles
    assert "historical_and_current_geographies_not_silently_merged" in principles
    assert module["engineering"]["fuzzy_linking"] == "prohibited"
    assert module["engineering"]["missing_numeric_policy"] == "preserve_null_never_zero"
    sensitive = module["engineering"]["sensitive_data_policy"].lower()
    for forbidden in ["student lists", "pen numbers", "mobile numbers", "person-level"]:
        assert forbidden in sensitive


def test_discovered_education_sources_remain_nonpublishable_until_payload_and_rights_review():
    sources = _load(SOURCES)["sources"]
    assert sources
    for source in sources:
        assert source["publishable"] is False
        assert source["authority"]
        assert source["url"].startswith("https://")
        assert "rights_status" in source
        assert "acquisition_status" in source
    api = next(s for s in sources if s["id"] == "UDISE_PLUS_API_PORTAL")
    assert "reuse" in api["rights_status"]
    assert "pending" in api["acquisition_status"]
