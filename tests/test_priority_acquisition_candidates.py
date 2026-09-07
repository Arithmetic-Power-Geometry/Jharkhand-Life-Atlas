from pathlib import Path

import yaml


MODULE_FILES = {
    "water_access": Path("modules/water_access/acquisition_candidates.yaml"),
    "sanitation_hygiene": Path("modules/sanitation_hygiene/acquisition_candidates.yaml"),
    "education_access": Path("modules/education_access/acquisition_candidates.yaml"),
}


def _load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_priority_candidate_files_are_fail_closed():
    for module_id, path in MODULE_FILES.items():
        data = _load(path)
        assert data["schema"] == "JLA_ACQUISITION_CANDIDATES_V1"
        assert data["module_id"] == module_id
        assert data["publication_allowed"] is False
        assert data["candidates"]
        for candidate in data["candidates"]:
            state = candidate["acquisition_state"]
            assert "payload_not_acquired" in state or "selection_pending" in state
            required = set(candidate["required_before_use"])
            assert any(item in required for item in {"acquire_exact_payload", "acquire_exact_csv_payload"})
            assert "preserve_missing_as_null" in required


def test_water_state_context_cannot_be_disaggregated():
    data = _load(MODULE_FILES["water_access"])
    candidate = data["candidates"][0]
    assert candidate["resource_scope"] == "state_ut"
    assert "state_level_values_must_not_be_disaggregated_to_lower_geographies" in data["rules"]
    assert "state_level_resource_cannot_support_district_block_or_village_outputs" in candidate["limitations"]


def test_sanitation_historical_candidate_requires_temporal_crosswalk():
    data = _load(MODULE_FILES["sanitation_hygiene"])
    historical = next(c for c in data["candidates"] if c["candidate_role"] == "historical_district_context")
    required = set(historical["required_before_use"])
    assert "identify_district_geography_vintage" in required
    assert "link_historical_districts_only_with_evidence_backed_crosswalk" in required
    assert "historical_and_current_geographies_are_not_silently_merged" in data["rules"]


def test_udise_candidate_requires_exact_year_codes_and_disclosure_review():
    data = _load(MODULE_FILES["education_access"])
    candidate = data["candidates"][0]
    required = set(candidate["required_before_use"])
    assert "select_exact_resource_and_academic_year" in required
    assert "verify_geography_vintage_for_state_district_block_codes" in required
    assert "suppress_or_aggregate_any_cells_that_raise_disclosure_risk" in required
    assert "exact_academic_year_must_be_explicit" in data["rules"]
