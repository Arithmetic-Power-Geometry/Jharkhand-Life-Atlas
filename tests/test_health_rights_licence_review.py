from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "modules" / "health_access" / "RIGHTS_LICENCE_REVIEW.md"
GATE = ROOT / "modules" / "health_access" / "completion_gate.yaml"


def test_health_rights_review_is_fail_closed_and_source_scoped():
    text = REVIEW.read_text(encoding="utf-8")
    assert "Government Open Data License - India" in text
    assert "each payload remains separately gated" in text
    assert "Excluded from publication" in text
    assert "Person-level, patient-level" in text
    assert "Never expose person-level health data" in text
    assert "Missing source values remain null/blank representations" in text
    assert "names" in text and "current-LGD equivalence" in text
    assert "search result or filename is not sufficient" in text


def test_health_completion_gate_cites_governed_rights_review():
    gate = yaml.safe_load(GATE.read_text(encoding="utf-8"))
    rights = gate["criteria"]["rights_licence_review"]
    assert rights["satisfied"] is True
    assert "RIGHTS_LICENCE_REVIEW.md" in rights["evidence"]
    assert gate["status"] == "open"
