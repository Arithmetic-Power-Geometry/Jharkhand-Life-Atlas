from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "modules" / "health_access" / "resource_identity_registry.yaml"


def load_registry():
    return yaml.safe_load(PATH.read_text(encoding="utf-8"))


def test_health_resource_identity_registry_stays_fail_closed():
    data = load_registry()
    assert data["registry_id"] == "JLA_HEALTH_RESOURCE_IDENTITY_V1"
    assert len(data["resources"]) >= 2
    for resource in data["resources"]:
        assert resource["canonical_resource_url"].startswith("https://")
        assert resource["machine_payload_identity_state"] == "unresolved"
        assert resource["raw_payload_acquired"] is False
        assert resource["raw_sha256"] is None
        assert resource["raw_bytes"] is None
        assert resource["schema_inspected"] is False
        assert resource["publication_allowed"] is False


def test_registry_forbids_guessing_machine_identifiers():
    rules = set(load_registry()["rules"])
    assert "canonical_resource_page_is_not_machine_payload" in rules
    assert "catalog_data_api_button_does_not_establish_api_identifier" in rules
    assert "never_construct_resource_uuid_from_title_or_slug" in rules
    assert "never_construct_api_endpoint_without_authoritative_identifier" in rules
    assert "successful_byte_retrieval_and_hash_are_required_before_acquired_status" in rules
    assert "missing_values_remain_null" in rules
    assert "no_person_level_health_data" in rules


def test_priority_health_resources_have_distinct_canonical_slugs():
    resources = load_registry()["resources"]
    slugs = [r["canonical_slug"] for r in resources]
    assert len(slugs) == len(set(slugs))
    assert any("nin-health-faclities" in slug for slug in slugs)
    assert any("national-hospital-directory" in slug for slug in slugs)
