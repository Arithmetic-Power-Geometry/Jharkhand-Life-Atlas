import hashlib
import json

import pytest

from jla.acquisition_receipt import build_acquisition_receipt, build_source_snapshot_draft
from jla.source_snapshot import source_snapshot_is_acquired, validate_source_snapshot


def test_csv_receipt_hashes_bytes_and_counts_jharkhand_without_mutation(tmp_path):
    payload = "state_name,facility,value\nJharkhand,A,\njharkhand,B,0\nBihar,C,5\n"
    path = tmp_path / "health.csv"
    path.write_text(payload, encoding="utf-8")

    receipt = build_acquisition_receipt(path, state_field="state_name")

    assert receipt["retrieval"]["byte_count"] == len(payload.encode("utf-8"))
    assert receipt["retrieval"]["sha256"] == hashlib.sha256(payload.encode("utf-8")).hexdigest()
    observed = receipt["observed_payload"]
    assert observed["observed_schema"] == ["state_name", "facility", "value"]
    assert observed["record_count_before_jharkhand_filter"] == 3
    assert observed["record_count_after_jharkhand_filter"] == 2
    assert observed["null_semantics_reviewed"] is False
    assert path.read_text(encoding="utf-8") == payload


def test_json_records_receipt_preserves_union_schema(tmp_path):
    payload = {"records": [{"State": "Jharkhand", "district": "Ranchi", "beds": None}, {"State": "Bihar", "district": "Gaya", "category": "DH"}]}
    path = tmp_path / "hospitals.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    receipt = build_acquisition_receipt(path, state_field="State")

    assert receipt["retrieval"]["media_type"] == "application/json"
    assert receipt["observed_payload"]["observed_schema"] == ["State", "district", "beds", "category"]
    assert receipt["observed_payload"]["record_count_after_jharkhand_filter"] == 1


def test_receipt_fails_closed_without_explicit_state_field(tmp_path):
    path = tmp_path / "source.csv"
    path.write_text("region,value\nJharkhand,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="state field not found"):
        build_acquisition_receipt(path, state_field="state_name")


def test_receipt_rejects_empty_and_unsupported_payloads(tmp_path):
    empty = tmp_path / "empty.csv"
    empty.write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        build_acquisition_receipt(empty, state_field="state")
    unsupported = tmp_path / "source.xlsx"
    unsupported.write_bytes(b"not-an-xlsx")
    with pytest.raises(ValueError, match="only CSV and JSON"):
        build_acquisition_receipt(unsupported, state_field="state")


def test_snapshot_draft_matches_contract_shape_but_cannot_self_publish(tmp_path):
    path = tmp_path / "health.csv"
    path.write_text("State,facility_id,beds\nJharkhand,H1,\nBihar,H2,10\n", encoding="utf-8")
    draft = build_source_snapshot_draft(
        path,
        module_id="health_access",
        source_id="TEST_HEALTH",
        source_title="Test public health payload",
        publisher="Government test publisher",
        authoritative_source_url="https://example.gov/catalog",
        exact_resource_or_api_url="https://example.gov/resource.csv",
        retrieved_at_utc="2026-09-08T00:00:00Z",
        retrieval_method="official_csv_download",
        publication_class="OPEN_WITH_ATTRIBUTION",
        licence_or_terms="Government Open Data License - India",
        licence_url_or_terms_url="https://example.gov/licence",
        attribution_requirement="required",
        source_reference_period="2026-08",
        source_geography_vintage="source_declared_current",
        smallest_authoritative_reusable_granularity="facility",
        source_record_identity_field_or_strategy="facility_id",
        state_field="State",
    )
    assert draft["contract"] == "JLA_SOURCE_SNAPSHOT_V1"
    assert draft["observed_payload"]["record_count_after_jharkhand_filter"] == 1
    assert draft["observed_payload"]["null_semantics_reviewed"] is False
    assert draft["missing_values_converted_to_zero"] is False
    assert draft["contains_sensitive_person_level_data"] is False
    assert source_snapshot_is_acquired(draft) is False
    errors = validate_source_snapshot(draft)
    assert "rights.rights_review_status is not verified" in errors
    assert "observed_payload.null_semantics_reviewed must be true" in errors
    assert any(error.startswith("validation.") for error in errors)
