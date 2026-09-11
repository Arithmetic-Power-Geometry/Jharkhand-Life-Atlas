from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]

CASES = (
    ("water_access", "census_water_access_2011", 27),
    ("sanitation_hygiene", "census_sanitation_hygiene_2011", 11),
    ("education_access", "census_education_access_2011", 40),
)


def test_priority_completion_gates_track_validated_historical_provenance() -> None:
    for module, stem, expected_fields in CASES:
        provenance_path = ROOT / "data" / "curated" / module / f"{stem}.provenance.json"
        gate_path = ROOT / "modules" / module / "completion_gate.yaml"

        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        gate = yaml.safe_load(gate_path.read_text(encoding="utf-8"))
        historical = gate["verified_partial_evidence"]["historical_census_2011"]

        assert gate["status"] == "open"
        assert provenance["status"] == "validated_source_native_historical_extract"
        assert historical["status"] == provenance["status"]
        assert historical["data"] == provenance["output"]
        assert historical["provenance"] == str(provenance_path.relative_to(ROOT))
        assert historical["row_count"] == provenance["row_count"] == 32394
        assert historical["reference_year"] == provenance["reference_year"] == 2011
        assert historical["thematic_field_count"] == provenance["thematic_field_count"] == expected_fields
        assert provenance["source_sha256"]
        assert provenance["output_sha256"]
        assert "missing" in provenance["missing_rule"].lower()
        assert "zero" in provenance["missing_rule"].lower()
        assert "no current-geography equivalence inferred" in provenance["geography_rule"]


def test_priority_gates_do_not_promote_historical_evidence_to_full_completion() -> None:
    for module, _, _ in CASES:
        gate_path = ROOT / "modules" / module / "completion_gate.yaml"
        gate = yaml.safe_load(gate_path.read_text(encoding="utf-8"))
        criteria = gate["criteria"]

        assert gate["status"] == "open"
        assert criteria["authoritative_acquisition"]["satisfied"] is False
        assert criteria["geographic_linkage"]["satisfied"] is False
        assert criteria["indicators"]["satisfied"] is False
        assert criteria["validation"]["satisfied"] is False
        assert criteria["downloadable_data_reports"]["satisfied"] is False
        assert criteria["green_ci_on_main"]["satisfied"] is False
        assert criteria["streamlit_presentation"]["satisfied"] is True
