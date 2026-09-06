from pathlib import Path
import csv

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
        assert source["license_review_status"].startswith("reviewed_")
        assert "ogdl" in source["license_review_status"]
        assert source["attribution_required"] is True
        assert source["license_checked_on"]


def test_restricted_current_registry_is_not_publishable_yet():
    sources = {s["source_id"]: s for s in _load("sources.yaml")["sources"]}
    hfr = sources["ABDM_HFR"]
    assert hfr["publication_class"] == "RESTRICTED"
    assert hfr["license_review_status"] == "rights_and_export_mechanism_pending"


def test_newest_official_geocoded_facility_source_is_preferred_but_not_claimed_ingested():
    sources = {s["source_id"]: s for s in _load("sources.yaml")["sources"]}
    newest = sources["OGD_NIN_HEALTH_FACILITIES_GEO_2026"]
    assert newest["resource_updated_on"].isoformat() == "2026-08-11"
    assert newest["granularity"] == "facility"
    assert "data_api" in newest["advertised_access"]
    assert newest["publication_class"] == "OPEN_WITH_ATTRIBUTION"


def test_health_schema_preserves_missing_and_source_grain():
    schema = _load("schema.yaml")["tables"]
    facilities = schema["health_facilities"]
    service = schema["health_service_activity"]
    assert facilities["grain"] == "one_source_facility_record"
    assert any("null, never zero" in rule for rule in facilities["rules"])
    assert any("District HMIS values must not be allocated" in rule for rule in service["rules"])


def test_health_source_coverage_is_fail_closed_and_auditable():
    path = MODULE / "source_coverage.csv"
    assert path.exists()
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    by_id = {row["source_id"]: row for row in rows}
    required = {
        "CENSUS_DCHB_JH_2011_HEALTH",
        "OGD_HEALTH_CENTRES_DIRECTORY",
        "OGD_NIN_HEALTH_FACILITIES_GEO_2026",
        "OGD_NHP_HOSPITAL_GEO_2025",
        "OGD_HMIS_JH_DISTRICT",
        "ABDM_HFR",
    }
    assert required.issubset(by_id)
    for row in rows:
        assert row["catalog_or_resource_verified"] in {"yes", "no"}
        assert row["raw_file_ingested"] in {"yes", "no"}
        assert row["curated_output_published"] in {"yes", "no"}
    assert by_id["OGD_NIN_HEALTH_FACILITIES_GEO_2026"]["raw_file_ingested"] == "no"
    assert by_id["OGD_NIN_HEALTH_FACILITIES_GEO_2026"]["curated_output_published"] == "no"
    assert by_id["OGD_NIN_HEALTH_FACILITIES_GEO_2026"]["publication_status"] == "pending_exact_api_or_csv_acquisition"
    assert by_id["OGD_NHP_HOSPITAL_GEO_2025"]["raw_file_ingested"] == "no"
    assert by_id["OGD_NHP_HOSPITAL_GEO_2025"]["curated_output_published"] == "no"
    assert by_id["OGD_HMIS_JH_DISTRICT"]["raw_file_ingested"] == "no"
    assert by_id["ABDM_HFR"]["publication_status"] == "blocked_rights_and_export"
