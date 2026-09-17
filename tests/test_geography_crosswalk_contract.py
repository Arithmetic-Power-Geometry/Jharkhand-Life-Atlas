import json
from pathlib import Path


def test_shared_geography_crosswalk_contract_is_fail_closed():
    path = Path("modules/core_geography/geography_crosswalk_contract.json")
    contract = json.loads(path.read_text(encoding="utf-8"))

    assert contract["service"] == "shared_geography_crosswalk"
    assert contract["publication_default"] == "fail_closed"
    rules = contract["publication_rules"]
    assert rules["name_only_match_allowed"] is False
    assert rules["fuzzy_name_match_allowed"] is False
    assert rules["missing_code_implies_equivalence"] is False
    assert rules["cross_vintage_join_requires_verified_record"] is True
    assert rules["verified_record_requires_evidence_reference"] is True
    assert rules["one_to_many_must_be_explicit"] is True
    assert rules["many_to_one_must_be_explicit"] is True
    assert rules["unknown_relation_remains_null"] is True
    assert contract["privacy"]["person_level_data_allowed"] is False


def test_crosswalk_contract_requires_vintages_codes_and_evidence():
    contract = json.loads(
        Path("modules/core_geography/geography_crosswalk_contract.json").read_text(encoding="utf-8")
    )
    required = set(contract["required_fields"])
    assert {
        "source_system", "source_vintage", "source_level", "source_code",
        "target_system", "target_vintage", "target_level", "target_code",
        "relation", "evidence_type", "evidence_reference", "review_status",
    } <= required
    assert "verified" in contract["allowed_review_status"]
