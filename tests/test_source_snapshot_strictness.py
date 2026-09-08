from copy import deepcopy

from jla.source_snapshot import source_snapshot_is_acquired, validate_source_snapshot


def _valid_snapshot():
    return {
        "contract": "JLA_SOURCE_SNAPSHOT_V1",
        "source_identity": {
            "module_id": "health_access",
            "source_id": "TEST_HEALTH",
            "source_title": "Test source",
            "publisher": "Government publisher",
            "authoritative_source_url": "https://example.gov/catalog",
            "exact_resource_or_api_url": "https://example.gov/resource.csv",
        },
        "retrieval": {
            "retrieved_at_utc": "2026-09-08T00:00:00Z",
            "retrieval_method": "official_csv_download",
            "media_type": "text/csv",
            "byte_count": 123,
            "sha256": "a" * 64,
        },
        "rights": {
            "publication_class": "OPEN_WITH_ATTRIBUTION",
            "licence_or_terms": "Government Open Data License - India",
            "licence_url_or_terms_url": "https://example.gov/licence",
            "rights_review_status": "verified",
            "attribution_requirement": "required",
        },
        "temporal_geographic_context": {
            "source_reference_period": "2026-08",
            "source_geography_vintage": "source_declared_current",
            "smallest_authoritative_reusable_granularity": "facility",
        },
        "observed_payload": {
            "observed_schema": ["State", "facility_id"],
            "record_count_before_jharkhand_filter": 10,
            "jharkhand_filter_method": "exact normalized State == Jharkhand",
            "record_count_after_jharkhand_filter": 4,
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


def test_well_formed_snapshot_can_pass_minimum_acquisition_contract():
    snapshot = _valid_snapshot()
    assert validate_source_snapshot(snapshot) == []
    assert source_snapshot_is_acquired(snapshot) is True


def test_wrong_or_missing_contract_id_fails_closed():
    for value in (None, "JLA_SOURCE_SNAPSHOT_V0", ""):
        snapshot = _valid_snapshot()
        if value is None:
            snapshot.pop("contract")
        else:
            snapshot["contract"] = value
        assert "contract must equal JLA_SOURCE_SNAPSHOT_V1" in validate_source_snapshot(snapshot)


def test_retrieval_timestamp_must_be_explicit_utc():
    for value in ("2026-09-08", "2026-09-08T00:00:00+05:30", "not-a-time"):
        snapshot = _valid_snapshot()
        snapshot["retrieval"]["retrieved_at_utc"] = value
        assert any("retrieval.retrieved_at_utc" in error for error in validate_source_snapshot(snapshot))


def test_boolean_values_cannot_masquerade_as_integer_counts():
    snapshot = _valid_snapshot()
    snapshot["retrieval"]["byte_count"] = True
    snapshot["observed_payload"]["record_count_before_jharkhand_filter"] = True
    errors = validate_source_snapshot(snapshot)
    assert "retrieval.byte_count must be a positive integer" in errors
    assert "observed_payload record count before must be a non-negative integer" in errors


def test_source_and_rights_urls_must_be_http_urls():
    snapshot = _valid_snapshot()
    snapshot["source_identity"]["exact_resource_or_api_url"] = "resource.csv"
    snapshot["rights"]["licence_url_or_terms_url"] = "file:///tmp/licence"
    errors = validate_source_snapshot(snapshot)
    assert "source_identity.exact_resource_or_api_url must be an http(s) URL" in errors
    assert "rights.licence_url_or_terms_url must be an http(s) URL" in errors


def test_split_crosswalk_cannot_be_verified_as_direct_linkage():
    snapshot = deepcopy(_valid_snapshot())
    snapshot["temporal_crosswalk"] = {
        "crosswalk_source": "Authoritative notification",
        "crosswalk_evidence_url": "https://example.gov/crosswalk",
        "relationship_type": "split",
        "review_status": "verified_split",
    }
    errors = validate_source_snapshot(snapshot)
    assert "unresolved temporal relationship cannot be marked as verified direct geography linkage" in errors
