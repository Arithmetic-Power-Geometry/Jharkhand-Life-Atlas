import json
from pathlib import Path


RECEIPT = Path("modules/health_access/evidence/nhd_metadata_surface_divergence_2026-09-16.json")


def test_nhd_metadata_divergence_receipt_remains_fail_closed():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    assert receipt["contract"] == "JLA_HEALTH_NHD_METADATA_SURFACE_DIVERGENCE_V1"
    assert receipt["status"] == "authoritative_metadata_surfaces_diverge_fail_closed"
    assert receipt["publication_allowed"] is False

    observations = receipt["observations"]
    assert observations["catalog_resource_listing_observed_updated_on"] != observations["resource_surface_observed_updated_on"]

    interpretation = receipt["interpretation"]
    assert interpretation["metadata_surface_divergence_verified"] is True
    assert interpretation["record_level_reference_period_verified"] is False
    assert interpretation["catalog_or_resource_updated_on_may_be_used_as_record_date"] is False
    assert interpretation["monthly_granularity_may_be_used_as_record_date"] is False
    assert interpretation["payload_freshness_inferred_from_metadata"] is False
    assert interpretation["canonical_payload_identity_resolved"] is False

    boundary = receipt["scientific_boundary"]
    assert boundary["metadata_drift_is_not_payload_drift"] is True
    assert boundary["metadata_drift_is_not_record_temporal_semantics"] is True
    assert boundary["no_current_indicator_authorization"] is True
    assert boundary["no_geography_equivalence_authorization"] is True
    assert boundary["missing_remains_null"] is True
    assert boundary["publication_gate_remains_closed"] is True
