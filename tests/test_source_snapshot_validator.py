from copy import deepcopy

from jla.source_snapshot import source_snapshot_is_acquired, validate_source_snapshot


def valid_snapshot():
    return {
        "source_identity": {
            "module_id": "health_access",
            "source_id": "TEST_SOURCE",
            "source_title": "Authoritative test source",
            "publisher": "Government publisher",
            "authoritative_source_url": "https://example.gov.in/catalog",
            "exact_resource_or_api_url": "https://example.gov.in/resource.csv",
        },
        "retrieval": {
            "retrieved_at_utc": "2026-09-07T15:00:00Z",
            "retrieval_method": "https_download",
            "media_type": "text/csv",
            "byte_count": 123,
            "sha256": "a" * 64,
        },
        "rights": {
            "publication_class": "open",
            "licence_or_terms": "Government Open Data License - India",
            "licence_url_or_terms_url": "https://example.gov.in/licence",
            "rights_review_status": "verified",
            "attribution_requirement": "attribute source",
        },
        "temporal_geographic_context": {
            "source_reference_period": "2026-08",
            "source_geography_vintage": "current",
            "smallest_authoritative_reusable_granularity": "facility",
        },
        "observed_payload": {
            "observed_schema": ["facility_id", "district_code"],
            "record_count_before_jharkhand_filter": 100,
            "jharkhand_filter_method": "state_code",
            "record_count_after_jharkhand_filter": 12,
            "source_record_identity_field_or_strategy": "facility_id",
            "null_semantics_reviewed": True,
        },
        "validation": {
            "schema_validation_status": "verified",
            "geography_linkage_status": "verified",
            "provenance_validation_status": "verified",
            "module_tests_status": "passed",
        },
        "missing_values_converted_to_zero": False,
        "contains_sensitive_person_level_data": False,
    }


def test_valid_snapshot_can_be_treated_as_acquired():
    snapshot = valid_snapshot()
    assert validate_source_snapshot(snapshot) == []
    assert source_snapshot_is_acquired(snapshot)


def test_catalog_style_placeholder_fails_closed():
    snapshot = valid_snapshot()
    snapshot["retrieval"]["byte_count"] = None
    snapshot["retrieval"]["sha256"] = None
    snapshot["observed_payload"]["observed_schema"] = []
    errors = validate_source_snapshot(snapshot)
    assert errors
    assert not source_snapshot_is_acquired(snapshot)


def test_missing_to_zero_shortcut_is_rejected():
    snapshot = valid_snapshot()
    snapshot["missing_values_converted_to_zero"] = True
    assert any("missing values" in error for error in validate_source_snapshot(snapshot))


def test_split_geography_cannot_be_verified_as_direct_linkage():
    snapshot = valid_snapshot()
    snapshot["temporal_crosswalk"] = {
        "crosswalk_source": "official notification",
        "crosswalk_evidence_url": "https://example.gov.in/crosswalk",
        "relationship_type": "split",
        "review_status": "reviewed",
    }
    assert any("unresolved temporal relationship" in error for error in validate_source_snapshot(snapshot))


def test_equivalent_geography_requires_verified_equivalent_review():
    snapshot = valid_snapshot()
    snapshot["temporal_crosswalk"] = {
        "crosswalk_source": "official notification",
        "crosswalk_evidence_url": "https://example.gov.in/crosswalk",
        "relationship_type": "equivalent",
        "review_status": "reviewed",
    }
    assert any("verified_equivalent" in error for error in validate_source_snapshot(snapshot))


def test_sensitive_person_level_snapshot_is_rejected():
    snapshot = deepcopy(valid_snapshot())
    snapshot["contains_sensitive_person_level_data"] = True
    assert not source_snapshot_is_acquired(snapshot)
