import hashlib
import json
import re
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
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _ledger():
    return json.loads(Path("modules/health_access/source_readiness.json").read_text(encoding="utf-8"))


def _sha256(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repository_path(path_value):
    path = Path(path_value)
    assert not path.is_absolute(), path_value
    assert ".." not in path.parts, path_value
    return path


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
            path = _repository_path(evidence_path)
            assert path.is_file(), (source_id, evidence_path)


def test_publication_ready_source_has_immutable_curated_provenance():
    """Recompute hashes and require both provenance endpoints to be governed evidence."""
    ledger = _ledger()
    for source_id, source in ledger["sources"].items():
        if not source["publication_ready"]:
            continue

        evidence = source.get("evidence", [])
        provenance_paths = [_repository_path(p) for p in evidence if p.endswith(".provenance.json")]
        assert provenance_paths, f"{source_id}: publication-ready source lacks provenance JSON"

        for provenance_path in provenance_paths:
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            output_path = _repository_path(provenance["output"])
            source_path = _repository_path(provenance["source"])

            assert provenance["output"] in evidence, (
                source_id,
                "curated output must be explicitly admitted in source-readiness evidence",
            )
            assert provenance["source"] in evidence, (
                source_id,
                "provenance source bytes must be explicitly admitted in source-readiness evidence",
            )
            assert output_path.is_file(), (source_id, provenance["output"])
            assert source_path.is_file(), (source_id, provenance["source"])
            assert SHA256_RE.fullmatch(provenance["output_sha256"]), source_id
            assert SHA256_RE.fullmatch(provenance["source_sha256"]), source_id
            assert _sha256(output_path) == provenance["output_sha256"], (source_id, provenance["output"])
            assert _sha256(source_path) == provenance["source_sha256"], (source_id, provenance["source"])
            assert provenance["row_count"] > 0, source_id
            assert "never converted to zero" in provenance["missing_rule"], source_id
            assert "no current-geography equivalence inferred" in provenance["geography_rule"], source_id


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
