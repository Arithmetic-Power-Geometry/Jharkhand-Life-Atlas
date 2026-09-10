from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "modules" / "health_access" / "release_manifest.yaml"


def _manifest():
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def test_health_release_manifest_remains_fail_closed():
    data = _manifest()
    assert data["module_id"] == "health_access"
    assert data["status"] == "IN_DEVELOPMENT"
    assert data["hard_invariants"]["missing_to_zero"] == "forbidden"
    assert data["hard_invariants"]["person_level_health_data"] == "forbidden"
    assert data["hard_invariants"]["district_to_village_allocation"] == "forbidden"
    assert data["hard_invariants"]["name_only_geography_equivalence"] == "forbidden"
    assert "exact_main_head_ci_green" in data["completion_requirements"]


def test_published_health_evidence_is_historical_and_provenance_gated():
    data = _manifest()
    published = data["published_evidence"]
    assert len(published) == 1
    item = published[0]
    assert item["evidence_id"] == "CENSUS_DCHB_JH_2011_HEALTH"
    assert item["reference_year"] == 2011
    assert item["geography_vintage"] == "Census_2011"
    assert item["row_count"] == 32394
    assert item["source_native_field_count"] == 69
    assert item["publication_state"] == "validated_source_native_historical_extract"
    assert "current_facility_inventory" in item["prohibited_claims"]
    assert "inferred_missing_as_zero" in item["prohibited_claims"]


def test_priority_health_sources_require_machine_evidence_before_publication():
    data = _manifest()
    queue = {item["source_id"]: item for item in data["priority_acquisition_queue"]}
    nin = queue["OGD_NIN_HEALTH_FACILITIES_GEO_2026"]
    required = set(nin["required_before_publication"])
    assert "exact_authoritative_machine_resource_identity" in required
    assert "observed_schema" in required
    assert "explicit_jharkhand_filter" in required
    assert "evidence_backed_geography_linkage" in required

    nhp = queue["OGD_NHP_HOSPITAL_GEO_2026"]
    assert "no_assumed_equivalence_with_NIN_resource" in nhp["required_before_publication"]
