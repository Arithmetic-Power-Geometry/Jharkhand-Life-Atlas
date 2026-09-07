from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "source_snapshot_contract.yaml"


def _contract():
    with CONTRACT.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_shared_source_snapshot_contract_is_active_and_fail_closed():
    contract = _contract()
    assert contract["contract_id"] == "JLA_SOURCE_SNAPSHOT_V1"
    assert contract["status"] == "active"

    principles = set(contract["principles"])
    assert "catalog_metadata_is_not_acquired_data" in principles
    assert "preview_rows_or_fields_are_not_full_schema_verification" in principles
    assert "immutable_snapshot_identity_precedes_cleaning" in principles
    assert "missing_values_remain_null_unless_source_explicitly_encodes_zero" in principles
    assert "historical_and_current_geographies_are_not_name_only_joined" in principles
    assert "person_level_sensitive_data_are_not_published" in principles


def test_acquired_sources_require_identity_hash_rights_schema_and_geography():
    required = _contract()["required_after_successful_acquisition"]

    assert {
        "module_id",
        "source_id",
        "source_title",
        "publisher",
        "authoritative_source_url",
        "exact_resource_or_api_url",
    } <= set(required["source_identity"])

    assert {"retrieved_at_utc", "byte_count", "sha256", "media_type"} <= set(
        required["retrieval"]
    )
    assert {"licence_or_terms", "rights_review_status", "attribution_requirement"} <= set(
        required["rights"]
    )
    assert {
        "source_reference_period",
        "source_geography_vintage",
        "smallest_authoritative_reusable_granularity",
    } <= set(required["temporal_geographic_context"])
    assert {
        "observed_schema",
        "record_count_before_jharkhand_filter",
        "record_count_after_jharkhand_filter",
        "null_semantics_reviewed",
    } <= set(required["observed_payload"])
    assert {
        "schema_validation_status",
        "geography_linkage_status",
        "provenance_validation_status",
        "module_tests_status",
    } <= set(required["validation"])


def test_temporal_crosswalk_gate_does_not_allow_name_only_equivalence():
    contract = _contract()
    crosswalk = contract["conditional_fields"]["temporal_crosswalk"]

    assert crosswalk["required_when_source_geography_differs_from_target"] is True
    assert set(crosswalk["required"]) >= {
        "crosswalk_source",
        "crosswalk_evidence_url",
        "relationship_type",
        "review_status",
    }
    assert crosswalk["publishable_direct_relationship"] == {
        "relationship_type": "equivalent",
        "review_status": "verified_equivalent",
    }
    assert {"split", "merge", "boundary_change", "unresolved"} <= set(
        crosswalk["unresolved_relationships"]
    )

    forbidden = set(contract["forbidden_shortcuts"])
    assert "fuzzy_or_name_only_temporal_geography_equivalence" in forbidden
    assert "converting_missing_to_zero_without_explicit_source_semantics" in forbidden
    assert "declaring_a_module_complete_from_source_discovery_alone" in forbidden
