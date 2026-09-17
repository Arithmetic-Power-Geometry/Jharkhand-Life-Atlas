import json
from pathlib import Path


REQUIRED = (
    "authoritative_payload",
    "immutable_hash",
    "schema_semantics",
    "temporal_interpretation",
    "geography_evidence",
    "rights_review",
    "privacy_review",
    "validated_curated_output",
)


def _ledger():
    return json.loads(Path("modules/health_access/source_readiness.json").read_text(encoding="utf-8"))


def test_health_source_readiness_is_fail_closed():
    ledger = _ledger()
    for source_id, source in ledger["sources"].items():
        assert all(field in source for field in REQUIRED), source_id
        if source["publication_ready"]:
            assert all(source[field] is True for field in REQUIRED), source_id
            assert source.get("evidence"), source_id
        else:
            assert source.get("blocker"), source_id


def test_publication_ready_source_evidence_is_repository_resident():
    ledger = _ledger()
    for source_id, source in ledger["sources"].items():
        if not source["publication_ready"]:
            continue
        evidence = source.get("evidence", [])
        assert evidence, source_id
        for evidence_path in evidence:
            path = Path(evidence_path)
            assert not path.is_absolute(), (source_id, evidence_path)
            assert ".." not in path.parts, (source_id, evidence_path)
            assert path.is_file(), (source_id, evidence_path)


def test_current_health_sources_are_not_promoted_without_payload_evidence():
    ledger = _ledger()
    for source_id, source in ledger["sources"].items():
        if source_id == "CENSUS2011_HEALTH_AMENITIES":
            continue
        assert source["publication_ready"] is False
        if not source["authoritative_payload"]:
            assert source["immutable_hash"] is False
            assert source["validated_curated_output"] is False


def test_hmis_district_source_preserves_geographic_scope():
    source = _ledger()["sources"]["OGD_HMIS_JH_DISTRICT"]
    assert "never be allocated to villages or facilities" in source["blocker"]
