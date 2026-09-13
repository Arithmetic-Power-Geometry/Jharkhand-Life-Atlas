from __future__ import annotations

import json
from pathlib import Path

from jla.privacy import privacy_risk_columns, public_projection_report


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "modules" / "health_access" / "national_hospital_directory_candidate_schema.json"
)


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_health_nhd_candidate_schema_matches_shared_privacy_governance() -> None:
    contract = _contract()
    header = contract["observed_columns"]
    assert isinstance(header, list)
    assert len(header) == contract["observed_column_count"] == 48

    observed_risk_names = [item["column"] for item in privacy_risk_columns(header)]
    assert observed_risk_names == contract["privacy_risk_columns"]
    assert set(contract["privacy_risk_columns"]).isdisjoint(
        contract["candidate_public_projection"]
    )

    report = public_projection_report(
        contract["candidate_public_projection"], source_header=header
    )
    assert report["privacy_gate_passed"] is True
    assert report["privacy_risk_columns"] == []
    assert report["missing_selected_columns"] == []
    assert report["row_values_inspected"] is False
    assert report["row_values_recorded"] is False


def test_health_nhd_candidate_contract_remains_noncanonical_and_fail_closed() -> None:
    contract = _contract()
    assert contract["contract"] == "JLA_HEALTH_NHD_CANDIDATE_SCHEMA_V1"
    assert contract["candidate_status"] == "non_canonical_candidate_evidence"
    assert contract["source_sha256"] == (
        "1ddcad9f9b922142a4374c7b89b70fb6cefd8a257448c70a61e1c07d98845134"
    )
    assert contract["source_byte_count"] == 10341256
    assert contract["observed_data_row_count"] == 30273
    assert contract["observed_row_width_mismatch_count"] == 0
    assert contract["publication_allowed"] is False
    assert contract["curated_dataset_emitted"] is False
    assert contract["geography_linkage_status"] == "unresolved"
    assert "uninterpreted source identifiers" in contract["source_identifier_semantics"]
    assert "State_ID" in contract["candidate_public_projection"]
    assert "District_ID" in contract["candidate_public_projection"]
