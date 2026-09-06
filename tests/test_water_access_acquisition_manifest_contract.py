from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "modules" / "water_access" / "acquisition_manifest_schema.yaml"


def _load_contract():
    return yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))


def test_water_acquisition_manifest_requires_reproducible_payload_provenance():
    contract = _load_contract()
    required = set(contract["required_fields"])
    assert {
        "source_id",
        "authoritative_resource_url",
        "retrieval_utc",
        "retrieval_method",
        "payload_sha256",
        "payload_bytes",
        "media_type",
        "licence",
        "licence_url",
        "schema_inspected",
        "source_geography_vintage",
        "smallest_authoritative_reusable_granularity",
        "person_level_sensitive_data_present",
    } <= required


def test_water_acquisition_contract_is_fail_closed_for_privacy_nulls_and_geography():
    contract = _load_contract()
    rules = "\n".join(contract["fail_closed_rules"]).lower()
    assert "missing source values to zero" in rules
    assert "person-level identifiers" in rules
    assert "current jjm" in rules and "census 2011" in rules
    assert "name equality alone" in rules
    assert "denominator" in rules


def test_water_acquisition_contract_does_not_treat_metadata_as_data():
    contract = _load_contract()
    purpose = contract["purpose"].lower()
    gate = contract["publication_gate"].lower()
    assert "not acquired payloads" in purpose
    assert "real manifest" in gate
    assert "in development" in gate
    assert "no factual water indicator" in gate
