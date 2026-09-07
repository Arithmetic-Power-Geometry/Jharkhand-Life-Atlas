from pathlib import Path

import yaml


MODULE_DIR = Path("modules/nutrition_food_security")


def load_yaml(name):
    return yaml.safe_load((MODULE_DIR / name).read_text(encoding="utf-8"))


def test_module7_is_active_but_not_complete():
    module = load_yaml("module.yaml")
    assert module["id"] == "nutrition_food_security"
    assert module["status"] != "complete"
    assert "core_geography" in module["dependencies"]
    assert module["engineering"]["fuzzy_linking"] == "prohibited"
    assert module["engineering"]["missing_numeric_policy"] == "preserve_null_never_zero"


def test_module7_completion_gate_is_fail_closed():
    gate = load_yaml("completion_gate.yaml")
    assert gate["status"] == "open"
    required = {
        "authoritative_acquisition",
        "rights_and_licence_review",
        "smallest_authoritative_reusable_granularity",
        "cleaning_and_schema",
        "geographic_linkage",
        "provenance",
        "indicators",
        "validation",
        "tests",
        "streamlit",
        "downloads_and_reports",
        "documentation",
        "green_ci_main",
    }
    assert required.issubset(gate["criteria"])
    assert all(not gate["criteria"][name]["passed"] for name in required)


def test_module7_sources_do_not_claim_unacquired_evidence():
    inventory = load_yaml("sources.yaml")
    assert inventory["review_status"] == "in_progress"
    sources = {s["source_id"]: s for s in inventory["sources"]}
    nfhs = sources["MOHFW_NFHS5_JHARKHAND_2019_21"]
    assert nfhs["authority_verified"] is True
    assert nfhs["exact_payload_acquired"] is False
    assert nfhs["publication_status"].startswith("blocked")
    poshan = sources["MWCD_POSHAN_TRACKER"]
    assert poshan["exact_payload_acquired"] is False
    assert "restricted" in poshan["privacy_class"]


def test_module7_privacy_and_scientific_red_lines_are_explicit():
    gate = load_yaml("completion_gate.yaml")
    privacy = " ".join(gate["privacy_red_lines"])
    scientific = set(gate["scientific_red_lines"])
    assert "beneficiary" in privacy
    assert "aadhaar" in privacy
    assert "no_authenticated_poshan_tracker_scraping" in gate["privacy_red_lines"]
    assert "missing_is_not_zero" in scientific
    assert "no_fabricated_denominators" in scientific
    assert "no_silent_historical_current_geography_merge" in scientific
