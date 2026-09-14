import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "modules" / "health_access" / "evidence" / "hmis_pakur_2019_20_november_acquisition_2026-09-14.json"


def _evidence():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_persisted_pakur_evidence_is_exact_and_fail_closed():
    e = _evidence()

    assert e["contract"] == "JLA_HEALTH_HMIS_PAKUR_ACQUISITION_EVIDENCE_V1"
    assert e["source_id"] == "OGD_HMIS_PAKUR_2019_20_NOVEMBER"
    assert e["workflow_head_sha"] == "0d4f0c58033ed84a12812549c10c6de88476e9d0"
    assert e["workflow_run_id"] == 34906143798
    assert e["workflow_conclusion"] == "success"
    assert e["resource_page_http_status"] == 200
    assert e["resource_page_bytes"] == 1001569
    assert e["resource_page_sha256"] == "7d1fcadbb0f6b906ff5bd21b8abcb1d3bcc2b0df5089fc2081e1dfa18bba2fc2"
    assert e["artifact_zip_sha256"] == "bce2e992e2dbf06bd35caaef2a2309115633804193a9d9b61bbc80e1f1a7011d"

    assert e["candidate_links"] == []
    assert e["raw_payload_acquired"] is False
    assert e["raw_sha256"] is None
    assert e["raw_byte_count"] is None
    assert e["observed_schema"] is None
    assert e["schema_inspected"] is False
    assert e["publication_allowed"] is False
    assert e["blocker"] == "no_explicit_authoritative_csv_payload_admitted_from_resource_page"


def test_pakur_evidence_preserves_period_provisionality_and_aggregation_level():
    e = _evidence()
    meta = e["authoritative_resource_metadata"]
    governance = e["governance"]

    assert meta["reference_period"] == "2019-20_november"
    assert meta["granularity"] == "Monthly"
    assert meta["resource_api_state"] == "does_not_exist"
    assert meta["provisional_figures"] is True
    assert meta["expected_columns"] == [
        "Indicator",
        "S.No.",
        "Parameters",
        "Type",
        "SubDistrict - _Pakur - Total [(A+B) or (C+D)]",
    ]

    assert governance["preserve_missing_as_null"] is True
    assert governance["allow_missing_to_zero_conversion"] is False
    assert governance["allow_downscaling_subdistrict_aggregates"] is False
    assert governance["allow_endpoint_inference_from_html_or_slug"] is False
    assert governance["allow_third_party_payload_substitution"] is False
    assert governance["provisional_status_must_be_preserved"] is True
    assert governance["publication_requires_verified_payload_schema_geography_and_indicator_gates"] is True
