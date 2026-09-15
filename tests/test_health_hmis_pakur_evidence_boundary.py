import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "modules" / "health_access" / "evidence" / "hmis_pakur_2019_20_november_acquisition_2026-09-14.json"


def _evidence():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_resource_page_evidence_cannot_be_promoted_to_dataset_evidence():
    e = _evidence()
    meta = e["authoritative_resource_metadata"]

    # An official HTML resource page is provenance evidence, not dataset bytes.
    assert e["evidence_kind"] == "authoritative_resource_page_acquisition_attempt"
    assert e["resource_page_http_status"] == 200
    assert e["resource_page_sha256"]
    assert e["resource_page_bytes"] > 0

    # Advertising CSV does not establish a downloadable payload identity.
    assert meta["advertised_format"].lower() == "csv"
    assert meta["advertised_file_size"] == "54 KB"
    assert e["candidate_links"] == []
    assert e["raw_payload_acquired"] is False
    assert e["raw_sha256"] is None
    assert e["raw_byte_count"] is None
    assert e["schema_inspected"] is False
    assert e["observed_schema"] is None


def test_expected_columns_are_not_misrepresented_as_observed_schema():
    e = _evidence()
    meta = e["authoritative_resource_metadata"]

    assert meta["expected_columns"]
    assert e["observed_schema"] is None
    assert e["schema_inspected"] is False
    assert e["publication_allowed"] is False


def test_pakur_temporal_metadata_does_not_authorize_cross_period_inference():
    e = _evidence()
    meta = e["authoritative_resource_metadata"]

    assert meta["reference_period"] == "2019-20_november"
    assert meta["granularity"] == "Monthly"
    assert meta["provisional_figures"] is True
    assert e["publication_allowed"] is False

    # The resource has a bounded historical reference period; it is not evidence
    # of current conditions, trends, or before/after effects without another
    # independently validated period and a valid geographic linkage.
    assert e["governance"]["publication_requires_verified_payload_schema_geography_and_indicator_gates"] is True
