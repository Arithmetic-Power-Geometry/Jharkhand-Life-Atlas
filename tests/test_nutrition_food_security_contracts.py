from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "nutrition_food_security"


def load_yaml(name: str):
    return yaml.safe_load((MODULE / name).read_text(encoding="utf-8"))


def test_schema_contract_is_fail_closed_and_privacy_preserving():
    c = load_yaml("schema_contract.yaml")
    assert c["module_id"] == "nutrition_food_security"
    assert c["production_schema_gate_satisfied"] is False
    assert c["null_policy"]["preserve_missing_as_null"] is True
    assert c["null_policy"]["zero_allowed_only_when_explicitly_reported_by_source"] is True
    assert c["geography"]["fuzzy_name_join"] == "prohibited"
    assert c["geography"]["current_to_census2011_name_only_join"] == "prohibited"
    assert c["indicator_integrity"]["survey_estimates_must_not_be_represented_as_administrative_counts"] is True
    prohibited = set(c["privacy"]["prohibited_fields"])
    assert {"aadhaar", "ration_card_number", "beneficiary_id", "household_id", "child_id", "mother_id"} <= prohibited
    assert "ci_green_on_main" in c["publication_gate"]["no_curated_output_may_be_labeled_research_ready_until"]


def test_acquisition_contract_requires_real_payload_evidence():
    c = load_yaml("acquisition_manifest_schema.yaml")
    assert c["state"] == "pre_acquisition"
    rules = c["verification_rules"]
    assert rules["sha256_required_for_acquired_verified"] is True
    assert rules["byte_count_required_for_acquired_verified"] is True
    assert rules["observed_schema_required_for_acquired_verified"] is True
    assert rules["catalog_metadata_is_not_payload"] is True
    assert rules["dashboard_visual_is_not_payload"] is True
    assert c["rights_rules"]["unclear_rights_fail_closed"] is True
    assert c["privacy_rules"]["person_level_records_prohibited"] is True
    assert c["geography_rules"]["census2011_and_current_geography_must_not_be_silently_merged"] is True
    assert c["geography_rules"]["name_only_crosswalk_prohibited"] is True
