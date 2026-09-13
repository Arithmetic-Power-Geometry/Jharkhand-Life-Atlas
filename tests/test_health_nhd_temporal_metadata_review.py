import json
from pathlib import Path


REVIEW = Path("modules/health_access/evidence/nhd_temporal_metadata_review_2026-09-14.json")
EXPECTED_SHA256 = "1ddcad9f9b922142a4374c7b89b70fb6cefd8a257448c70a61e1c07d98845134"


def _load_review():
    return json.loads(REVIEW.read_text(encoding="utf-8"))


def test_temporal_review_is_bound_to_verified_candidate_and_nonpublishing():
    review = _load_review()
    assert review["contract"] == "JLA_HEALTH_NHD_TEMPORAL_METADATA_REVIEW_V1"
    assert review["module"] == "health_access"
    assert review["publication_allowed"] is False
    binding = review["payload_binding"]
    assert binding["candidate_sha256"] == EXPECTED_SHA256
    assert binding["candidate_byte_count"] == 10_341_256
    assert binding["observed_data_row_count"] == 30_273
    assert binding["observed_column_count"] == 48


def test_resource_freshness_cannot_be_promoted_to_record_reference_period():
    review = _load_review()
    temporal = review["temporal_interpretation"]
    assert temporal["resource_page_update_date_is_observation_date_for_every_record"] is False
    assert temporal["resource_title_updated_till_last_month_establishes_record_level_reference_month"] is False
    assert temporal["declared_monthly_granularity_establishes_record_level_update_timestamp"] is False
    assert temporal["payload_download_time_establishes_record_reference_period"] is False
    assert temporal["record_level_reference_period_verified"] is False
    assert temporal["indicator_time_label_allowed"] is False
    assert temporal["cross_period_comparison_allowed"] is False


def test_official_blank_semantics_preserve_nulls_and_prohibit_zero_fill():
    review = _load_review()
    missing = review["missingness_interpretation"]
    assert missing["official_resource_note_treats_na_or_blank_as_not_available"] is True
    assert missing["blank_may_be_silently_converted_to_zero"] is False
    assert missing["blank_may_be_interpreted_as_absence_of_facility_or_service_without_field_specific_evidence"] is False
    assert "null" in missing["repository_null_policy"].lower()


def test_time_labelled_scientific_outputs_remain_blocked():
    review = _load_review()
    prohibited = "\n".join(review["prohibited_uses_before_temporal_resolution"]).lower()
    assert "2025" in prohibited
    assert "current or latest" in prohibited
    assert "time-series" in prohibited
    assert "verified temporal" in prohibited
    assert "authoritative evidence" in review["remaining_temporal_gate"].lower()
