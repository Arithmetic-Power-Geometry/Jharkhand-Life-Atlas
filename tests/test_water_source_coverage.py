from pathlib import Path
import csv
import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "water_access"


def load_yaml(name):
    return yaml.safe_load((MODULE / name).read_text(encoding="utf-8"))


def load_coverage():
    with (MODULE / "source_coverage.csv").open(encoding="utf-8", newline="") as handle:
        return {row["source_id"]: row for row in csv.DictReader(handle)}


def test_water_source_coverage_includes_all_registered_sources():
    coverage = load_coverage()
    source_ids = {source["id"] for source in load_yaml("sources.yaml")["sources"]}
    assert source_ids <= set(coverage)


def test_water_acquisition_candidates_use_registered_source_ids():
    source_ids = {source["id"] for source in load_yaml("sources.yaml")["sources"]}
    candidates = load_yaml("acquisition_candidates.yaml")["candidates"]
    for candidate in candidates:
        assert candidate["source_id"] in source_ids


def test_water_unacquired_sources_are_never_exposed_as_published():
    coverage = load_coverage()
    for row in coverage.values():
        assert row["catalog_or_resource_verified"] == "yes"
        if row["raw_file_ingested"] == "no":
            assert row["curated_output_published"] == "no"
            assert row["publication_status"].startswith(("pending_", "blocked_", "catalog_"))


def test_water_candidate_gate_remains_fail_closed_until_payload_acquisition():
    candidates = load_yaml("acquisition_candidates.yaml")
    assert candidates["publication_allowed"] is False
    coverage = load_coverage()
    for candidate in candidates["candidates"]:
        row = coverage[candidate["source_id"]]
        assert "payload_not_acquired" in candidate["acquisition_state"]
        assert row["raw_file_ingested"] == "no"
        assert row["curated_output_published"] == "no"
