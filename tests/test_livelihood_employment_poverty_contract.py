from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "livelihood_employment_poverty"


def load_yaml(name: str):
    return yaml.safe_load((MODULE / name).read_text(encoding="utf-8"))


def test_livelihood_module_is_fail_closed():
    module = load_yaml("module.yaml")
    gate = load_yaml("completion_gate.yaml")
    assert module["id"] == "livelihood_employment_poverty"
    assert module["status"] == "active"
    assert module["dependencies"] == ["core_geography"]
    assert module["engineering"]["fuzzy_linking"] == "prohibited"
    assert module["engineering"]["missing_numeric_policy"] == "preserve_null_never_zero"
    assert gate["complete"] is False
    assert all(value is False for value in gate["publication_gate"].values())
    assert gate["rules"]["person_level_worker_beneficiary_household_data_prohibited"] is True
    assert gate["rules"]["survey_estimates_must_not_be_presented_as_administrative_counts"] is True
    assert gate["rules"]["current_and_historical_geographies_must_not_be_silently_merged"] is True


def test_livelihood_sources_are_inventory_not_published_data():
    sources = load_yaml("sources.yaml")
    assert sources["publication_state"] == "in_development"
    assert sources["rights"]["policy"] == "fail_closed_per_resource"
    assert sources["geography"]["name_only_join"] == "prohibited"
    assert sources["privacy"]["aggregate_only"] is True
    assert sources["survey_governance"]["survey_estimate_as_admin_count"] == "prohibited"
    for source in sources["sources"]:
        assert source["payload_acquired"] is False
        assert source["rights_review_complete"] is False
