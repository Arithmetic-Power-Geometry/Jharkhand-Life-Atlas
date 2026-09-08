from pathlib import Path
import csv
import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "education_access"


def load_yaml(name):
    return yaml.safe_load((MODULE / name).read_text(encoding="utf-8"))


def load_coverage():
    with (MODULE / "source_coverage.csv").open(encoding="utf-8", newline="") as handle:
        return {row["source_id"]: row for row in csv.DictReader(handle)}


def test_education_source_coverage_includes_registered_sources_and_candidates():
    coverage = load_coverage()
    source_ids = {source["id"] for source in load_yaml("sources.yaml")["sources"]}
    candidate_ids = {candidate["source_id"] for candidate in load_yaml("acquisition_candidates.yaml")["candidates"]}
    assert source_ids | candidate_ids <= set(coverage)


def test_education_unacquired_evidence_is_never_exposed_as_published():
    coverage = load_coverage()
    for row in coverage.values():
        assert row["catalog_or_resource_verified"] == "yes"
        if row["raw_file_ingested"] == "no":
            assert row["curated_output_published"] == "no"
            assert row["publication_status"].startswith(("pending_", "blocked_", "catalog_"))


def test_education_candidate_gate_remains_fail_closed():
    candidates = load_yaml("acquisition_candidates.yaml")
    assert candidates["publication_allowed"] is False
    coverage = load_coverage()
    for candidate in candidates["candidates"]:
        state = candidate["acquisition_state"]
        assert "pending" in state
        row = coverage[candidate["source_id"]]
        assert row["raw_file_ingested"] == "no"
        assert row["curated_output_published"] == "no"
