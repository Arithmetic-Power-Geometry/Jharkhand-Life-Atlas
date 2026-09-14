from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "modules" / "health_access" / "audit_ogd_payload_candidate_equivalence.py"
WORKFLOW = ROOT / ".github" / "workflows" / "health-ogd-payload-equivalence.yml"


def _load_module():
    spec = importlib.util.spec_from_file_location("health_payload_equivalence_audit", AUDIT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record(url: str, digest: str, size: int, eligible: bool = True):
    return {
        "requested_url": url,
        "eligible_for_equivalence": eligible,
        "sha256": digest if eligible else None,
        "byte_count": size if eligible else None,
    }


def test_identical_authoritative_candidates_permit_only_identity_selection() -> None:
    module = _load_module()
    digest = "a" * 64
    result = module.evaluate_candidate_records([
        _record("https://data.gov.in/a.csv", digest, 123),
        _record("https://www.data.gov.in/b.csv", digest, 123),
    ])
    assert result["all_candidates_verified"] is True
    assert result["byte_identical"] is True
    assert result["canonical_selection_permitted"] is True
    assert result["shared_sha256"] == digest
    assert result["shared_byte_count"] == 123
    assert result["deterministic_preferred_candidate_url"] == "https://data.gov.in/a.csv"


def test_hash_mismatch_keeps_candidate_identity_ambiguous() -> None:
    module = _load_module()
    result = module.evaluate_candidate_records([
        _record("https://data.gov.in/a.csv", "a" * 64, 123),
        _record("https://www.data.gov.in/b.csv", "b" * 64, 123),
    ])
    assert result["all_candidates_verified"] is True
    assert result["byte_identical"] is False
    assert result["canonical_selection_permitted"] is False
    assert result["deterministic_preferred_candidate_url"] is None
    assert result["shared_sha256"] is None


def test_partial_retrieval_does_not_turn_missing_evidence_into_false_equivalence() -> None:
    module = _load_module()
    result = module.evaluate_candidate_records([
        _record("https://data.gov.in/a.csv", "a" * 64, 123),
        _record("https://www.data.gov.in/b.csv", "", 0, eligible=False),
    ])
    assert result["all_candidates_verified"] is False
    assert result["byte_identical"] is None
    assert result["canonical_selection_permitted"] is False
    assert result["deterministic_preferred_candidate_url"] is None


def test_identical_aliases_must_match_governed_payload_binding() -> None:
    module = _load_module()
    governed_digest = "a" * 64
    records = [
        _record("https://data.gov.in/a.csv", governed_digest, 123),
        _record("https://www.data.gov.in/b.csv", governed_digest, 123),
    ]
    result = module.evaluate_candidate_records(
        records,
        expected_sha256=governed_digest,
        expected_byte_count=123,
    )
    assert result["byte_identical"] is True
    assert result["governed_binding_required"] is True
    assert result["governed_binding_verified"] is True
    assert result["canonical_selection_permitted"] is True


def test_two_aliases_drifting_together_cannot_validate_governed_candidate() -> None:
    module = _load_module()
    drifted_digest = "b" * 64
    records = [
        _record("https://data.gov.in/a.csv", drifted_digest, 456),
        _record("https://www.data.gov.in/b.csv", drifted_digest, 456),
    ]
    result = module.evaluate_candidate_records(
        records,
        expected_sha256="a" * 64,
        expected_byte_count=123,
    )
    assert result["all_candidates_verified"] is True
    assert result["byte_identical"] is True
    assert result["governed_binding_verified"] is False
    assert result["canonical_selection_permitted"] is False
    assert result["deterministic_preferred_candidate_url"] is None
    assert result["shared_sha256"] == drifted_digest
    assert result["shared_byte_count"] == 456


def test_governed_binding_requires_hash_and_byte_count_together() -> None:
    module = _load_module()
    records = [
        _record("https://data.gov.in/a.csv", "a" * 64, 123),
        _record("https://www.data.gov.in/b.csv", "a" * 64, 123),
    ]
    try:
        module.evaluate_candidate_records(records, expected_sha256="a" * 64)
    except ValueError as exc:
        assert "supplied together" in str(exc)
    else:
        raise AssertionError("partial governed payload binding must fail closed")


def test_workflow_preserves_fail_closed_publication_boundary() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    required = [
        "JLA_OGD_PAYLOAD_CANDIDATE_EQUIVALENCE_V1",
        "publication_allowed'] is False",
        "raw_payload_acquired'] is False",
        "raw_snapshot_persisted'] is False",
        "schema_inspected'] is False",
        "multiple_candidates_require_all_successful_hashes_before_equivalence",
        "byte_equivalence_verification_is_not_raw_snapshot_acquisition",
        "byte_equivalence_verification_does_not_enable_publication",
        "--expected-sha256",
        "--expected-byte-count",
        "governed_binding_required",
        "governed_binding_verified",
        "two_official_aliases_drifting_together_do_not_validate_the_governed_candidate",
    ]
    missing = [item for item in required if item not in text]
    assert not missing, f"Health payload equivalence workflow lost fail-closed guards: {missing}"
