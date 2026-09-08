import csv
from pathlib import Path

import yaml


PRIORITY_MODULES = ("water_access", "sanitation_hygiene", "education_access")


def _rows(module_id):
    path = Path("modules") / module_id / "source_coverage.csv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_priority_candidate_sources_are_exposed_fail_closed():
    for module_id in PRIORITY_MODULES:
        candidate_path = Path("modules") / module_id / "acquisition_candidates.yaml"
        candidates = yaml.safe_load(candidate_path.read_text(encoding="utf-8"))
        assert candidates["publication_allowed"] is False

        rows = _rows(module_id)
        assert rows, f"{module_id} must expose source coverage in Streamlit"
        coverage_ids = {row["source_id"] for row in rows}
        candidate_ids = {item["source_id"] for item in candidates["candidates"]}
        assert candidate_ids <= coverage_ids

        for row in rows:
            assert row["catalog_or_resource_verified"].lower() == "yes"
            assert row["raw_file_ingested"].lower() == "no"
            assert row["curated_output_published"].lower() == "no"
            assert row["publication_status"].startswith("pending_")
            assert row["notes"].strip()


def test_priority_source_coverage_does_not_claim_lower_geography_from_context_only_sources():
    water = {row["source_id"]: row for row in _rows("water_access")}
    sanitation = {row["source_id"]: row for row in _rows("sanitation_hygiene")}

    assert water["OGD_JJM_STATE_STATUS_2025_01_29"]["geography"] == "state_ut"
    assert "disaggregated" in water["OGD_JJM_STATE_STATUS_2025_01_29"]["notes"].lower()
    assert sanitation["OGD_SBMG_IHHL_CSC_2024_25"]["geography"] == "state_ut"
    assert sanitation["OGD_SBMG_DISTRICT_IHHL_2017_18"]["geography"] == "state_ut_and_district"
