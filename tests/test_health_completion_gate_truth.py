import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "modules" / "health_access" / "completion_gate.yaml"
PROVENANCE = ROOT / "data" / "curated" / "health_access" / "census_health_access_2011.provenance.json"
REPORT = ROOT / "modules" / "health_access" / "HISTORICAL_EVIDENCE_REPORT.md"


def test_health_gate_acknowledges_validated_historical_evidence():
    gate = yaml.safe_load(GATE.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))

    historical = gate["verified_partial_evidence"]["historical_census_2011"]
    assert provenance["status"] == "validated_source_native_historical_extract"
    assert historical["status"] == provenance["status"]
    assert historical["row_count"] == provenance["row_count"] == 32394
    assert historical["health_field_count"] == provenance["health_field_count"] == 69
    assert historical["reference_year"] == provenance["reference_year"] == 2011
    assert historical["report"] == "modules/health_access/HISTORICAL_EVIDENCE_REPORT.md"
    assert REPORT.is_file()


def test_health_gate_remains_fail_closed_for_full_completion():
    gate = yaml.safe_load(GATE.read_text(encoding="utf-8"))
    assert gate["status"] != "complete"
    criteria = gate["criteria"]
    assert criteria["authoritative_acquisition"]["satisfied"] is False
    assert criteria["geographic_linkage"]["satisfied"] is False
    assert criteria["indicators"]["satisfied"] is False
    assert criteria["validation"]["satisfied"] is False
    assert criteria["downloadable_data_reports"]["satisfied"] is False


def test_health_gate_records_streamlit_historical_download_truth():
    gate = yaml.safe_load(GATE.read_text(encoding="utf-8"))
    presentation = gate["criteria"]["streamlit_presentation"]
    downloads = gate["criteria"]["downloadable_data_reports"]
    assert presentation["satisfied"] is True
    assert "validated Census 2011 Health dataset" in presentation["evidence"]
    assert downloads["satisfied"] is False
    evidence = downloads["evidence"]
    assert "historical Health CSV download" in evidence
    assert "research-ready historical evidence report" in evidence
    assert "additional validated production datasets/reports" in evidence
