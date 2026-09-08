from pathlib import Path
import csv
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "modules" / "health_access" / "resource_identity_registry.yaml"
COVERAGE_PATH = ROOT / "modules" / "health_access" / "source_coverage.csv"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def load_registry():
    return yaml.safe_load(PATH.read_text(encoding="utf-8"))


def load_coverage():
    with COVERAGE_PATH.open(encoding="utf-8", newline="") as handle:
        return {row["source_id"]: row for row in csv.DictReader(handle)}


def test_health_resource_identity_registry_is_transition_safe_and_fail_closed():
    data = load_registry()
    assert data["registry_id"] == "JLA_HEALTH_RESOURCE_IDENTITY_V1"
    assert len(data["resources"]) >= 2
    allowed_states = set(data["state_contract"])

    for resource in data["resources"]:
        assert resource["canonical_resource_url"].startswith("https://")
        state = resource["machine_payload_identity_state"]
        assert state in allowed_states

        if state == "unresolved":
            assert resource["machine_resource_id"] is None
            assert resource["machine_payload_url"] is None
            assert resource["identity_evidence_url"] is None
            assert resource["identity_verified_at"] is None
            assert resource["raw_payload_acquired"] is False
            assert resource["raw_sha256"] is None
            assert resource["raw_bytes"] is None
            assert resource["schema_inspected"] is False
            assert resource["publication_allowed"] is False

        if state in {"resolved_unretrieved", "acquired_verified"}:
            assert resource["machine_resource_id"]
            assert resource["machine_payload_url"].startswith("https://")
            assert resource["identity_evidence_url"].startswith("https://")
            assert resource["identity_verified_at"]

        if state == "resolved_unretrieved":
            assert resource["raw_payload_acquired"] is False
            assert resource["publication_allowed"] is False

        if state == "acquired_verified":
            assert resource["raw_payload_acquired"] is True
            assert isinstance(resource["raw_bytes"], int) and resource["raw_bytes"] > 0
            assert SHA256_RE.fullmatch(resource["raw_sha256"] or "")
            assert resource["schema_inspected"] is True


def test_catalog_api_identity_is_not_mistaken_for_resource_identity():
    data = load_registry()
    catalog = data["catalog_evidence"]
    assert catalog["catalog_api_id"] == "e48a8bcf-ff56-4f39-839d-095827ba2a18"
    assert catalog["catalog_api_url"].startswith("https://www.data.gov.in/apis/")
    assert catalog["catalog_api_identity_state"] == "verified_from_official_catalog_link"
    assert catalog["catalog_api_payload_retrieved"] is False
    for resource in data["resources"]:
        assert resource["machine_resource_id"] != catalog["catalog_api_id"]
        assert resource["raw_payload_acquired"] is False


def test_health_rights_review_records_godl_obligations_and_exclusions():
    rights = load_registry()["rights_evidence"]
    assert rights["platform_license"] == "Government Open Data License - India"
    assert rights["license_url"].startswith("https://data.gov.in/")
    obligations = set(rights["obligations"])
    assert {"acknowledge_data_provider", "acknowledge_source", "acknowledge_license"} <= obligations
    exclusions = set(rights["exclusions"])
    assert "personal_information" in exclusions
    assert "nonshareable_or_sensitive_data" in exclusions


def test_registry_forbids_guessing_machine_identifiers():
    rules = set(load_registry()["rules"])
    assert "canonical_resource_page_is_not_machine_payload" in rules
    assert "catalog_api_identity_is_not_resource_payload_identity" in rules
    assert "catalog_data_api_button_does_not_establish_api_identifier" in rules
    assert "never_construct_resource_uuid_from_title_or_slug" in rules
    assert "never_construct_api_endpoint_without_authoritative_identifier" in rules
    assert "machine_identity_requires_authoritative_evidence_url_and_verification_timestamp" in rules
    assert "successful_byte_retrieval_and_hash_are_required_before_acquired_status" in rules
    assert "publication_requires_shared_source_snapshot_gate" in rules
    assert "rights_review_does_not_substitute_for_payload_validation" in rules
    assert "missing_values_remain_null" in rules
    assert "no_person_level_health_data" in rules


def test_priority_health_resources_have_distinct_canonical_slugs():
    resources = load_registry()["resources"]
    slugs = [r["canonical_slug"] for r in resources]
    assert len(slugs) == len(set(slugs))
    assert any("nin-health-faclities" in slug for slug in slugs)
    assert any("national-hospital-directory" in slug for slug in slugs)


def test_health_source_coverage_cannot_outrun_resource_identity_registry():
    """Public coverage truth must never claim more evidence than the registry proves."""
    coverage = load_coverage()
    resources = load_registry()["resources"]

    for resource in resources:
        source_id = resource["source_id"]
        assert source_id in coverage, f"{source_id} missing from Health source_coverage.csv"
        row = coverage[source_id]

        assert row["catalog_or_resource_verified"] == "yes"
        expected_raw = "yes" if resource["raw_payload_acquired"] else "no"
        assert row["raw_file_ingested"] == expected_raw

        if resource["machine_payload_identity_state"] != "acquired_verified":
            assert row["curated_output_published"] == "no"
        if not resource["publication_allowed"]:
            assert row["curated_output_published"] == "no"


def test_health_coverage_publication_is_fail_closed_for_unacquired_priority_sources():
    coverage = load_coverage()
    priority_ids = {resource["source_id"] for resource in load_registry()["resources"]}

    for source_id in priority_ids:
        row = coverage[source_id]
        if row["raw_file_ingested"] == "no":
            assert row["curated_output_published"] == "no"
            assert row["publication_status"].startswith(("pending_", "blocked_", "catalog_"))
