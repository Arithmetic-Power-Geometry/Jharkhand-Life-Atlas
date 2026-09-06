from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "education_access"

REQUIRED = {
    "authoritative_acquisition",
    "rights_licence_review",
    "smallest_authoritative_reusable_granularity",
    "cleaning_engineering",
    "geographic_linkage",
    "provenance",
    "schema",
    "indicators",
    "validation",
    "tests",
    "streamlit_presentation",
    "downloadable_data_reports",
    "documentation",
    "green_ci_on_main",
}


def _load(path: str):
    return yaml.safe_load((MODULE / path).read_text(encoding="utf-8"))


def test_education_completion_gate_covers_strict_jla_protocol():
    gate = _load("completion_gate.yaml")
    assert gate["module"] == "education_access"
    assert REQUIRED == set(gate["criteria"])
    for item in gate["criteria"].values():
        assert isinstance(item["satisfied"], bool)
        assert item["evidence"].strip()


def test_education_cannot_claim_complete_with_open_gate():
    module = _load("module.yaml")
    gate = _load("completion_gate.yaml")
    all_satisfied = all(item["satisfied"] for item in gate["criteria"].values())
    if module["status"] == "complete":
        assert gate["status"] == "complete"
        assert all_satisfied
    else:
        assert not all_satisfied


def test_current_gate_records_real_education_publication_gaps():
    gate = _load("completion_gate.yaml")["criteria"]
    for key in [
        "authoritative_acquisition",
        "geographic_linkage",
        "schema",
        "indicators",
        "streamlit_presentation",
        "downloadable_data_reports",
    ]:
        assert gate[key]["satisfied"] is False
