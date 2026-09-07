from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "modules" / "health_access" / "source_resolution_contract.yaml"


def test_health_source_resolution_contract_fail_closed():
    c = yaml.safe_load(PATH.read_text(encoding="utf-8"))
    assert c["priority"] == "high"
    rules = c["fail_closed_rules"]
    assert rules["catalog_metadata_is_not_payload"] is True
    assert rules["dashboard_visual_is_not_payload"] is True
    assert rules["missing_is_not_zero"] is True
    assert rules["person_level_health_records_prohibited"] is True
    assert rules["unresolved_geography_must_not_be_fuzzy_joined"] is True
    assert rules["historical_current_geography_must_not_be_silently_merged"] is True
    hospital = next(t for t in c["resolution_tracks"] if t["id"] == "ogd_hospital_directory")
    assert hospital["current_state"] == "blocked_exact_payload_unresolved"
    assert "sha256" in hospital["required_before_acquired_verified"]
