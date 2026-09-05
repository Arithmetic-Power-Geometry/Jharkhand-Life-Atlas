from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "health_access"


def _load(name: str):
    return yaml.safe_load((MODULE / name).read_text(encoding="utf-8"))


def test_health_module_foundation_is_explicitly_active():
    module = _load("module.yaml")
    assert module["id"] == "health_access"
    assert module["status"] == "active"
    assert module["dependencies"] == ["core_geography"]
    assert "no_source_no_published_value" in module["principles"]
    assert "missing_is_not_zero" in module["principles"]


def test_open_ogd_health_sources_have_reviewed_license_metadata():
    sources = _load("sources.yaml")["sources"]
    ogd = [s for s in sources if s["source_id"].startswith("OGD_")]
    assert ogd
    for source in ogd:
        assert source["publication_class"] == "OPEN_WITH_ATTRIBUTION"
        assert source["license"] == "Government Open Data License - India"
        assert source["license_url"].startswith("https://www.data.gov.in/")
        assert source["license_review_status"].startswith("reviewed_ogdl")
        assert source["attribution_required"] is True
        assert source["license_checked_on"]


def test_restricted_current_registry_is_not_publishable_yet():
    sources = {s["source_id"]: s for s in _load("sources.yaml")["sources"]}
    hfr = sources["ABDM_HFR"]
    assert hfr["publication_class"] == "RESTRICTED"
    assert hfr["license_review_status"] == "rights_and_export_mechanism_pending"


def test_health_schema_preserves_missing_and_source_grain():
    schema = _load("schema.yaml")["tables"]
    facilities = schema["health_facilities"]
    service = schema["health_service_activity"]
    assert facilities["grain"] == "one_source_facility_record"
    assert any("null, never zero" in rule for rule in facilities["rules"])
    assert any("District HMIS values must not be allocated" in rule for rule in service["rules"])
