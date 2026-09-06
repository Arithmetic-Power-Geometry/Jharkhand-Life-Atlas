from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "modules" / "water_access" / "schema_contract.yaml"


def _contract():
    return yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))


def test_water_schema_contract_is_explicitly_prepublication():
    c = _contract()
    assert c["module"] == "water_access"
    assert c["status"] == "prepublication_contract"
    rules = c["publication_rules"]
    assert any("does not authorize publication" in r for r in rules)
    assert any("authoritative payload acquisition" in r for r in rules)


def test_water_schema_contract_preserves_missingness_and_true_zero_semantics():
    numeric = _contract()["numeric_semantics"]
    assert numeric["missing_policy"] == "preserve_null"
    assert numeric["zero_policy"] == "zero_only_when_source_explicitly_reports_zero"
    assert numeric["coercion_policy"] == "parse_failures_become_validation_errors_not_zero"


def test_water_schema_contract_blocks_unsafe_geographic_matching():
    geo = _contract()["geographic_linkage"]
    assert "authoritative_identifier" in geo["allowed_linkage_methods"]
    assert "verified_temporal_crosswalk" in geo["allowed_linkage_methods"]
    assert "fuzzy_name_match" in geo["prohibited_linkage_methods"]
    assert "silent_name_equivalence_across_vintages" in geo["prohibited_linkage_methods"]
    assert geo["historical_current_merge_policy"] == "prohibited_without_evidence_backed_crosswalk"


def test_water_schema_contract_prohibits_person_level_identifiers():
    privacy = _contract()["privacy"]
    assert privacy["person_level_records"] == "prohibited"
    assert privacy["beneficiary_identifiers"] == "prohibited"
    assert privacy["aadhaar_or_equivalent_identifiers"] == "prohibited"


def test_water_schema_contract_requires_reproducible_provenance():
    required = set(_contract()["provenance_requirements"])
    assert {
        "retrieval_url_or_endpoint",
        "retrieval_timestamp",
        "payload_hash",
        "source_licence_or_terms_reference",
        "transformation_version",
        "geography_linkage_method",
    } <= required
