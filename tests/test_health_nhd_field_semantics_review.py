import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "modules" / "health_access" / "evidence" / "nhd_field_semantics_review_2026-09-15.json"
EXPECTED_SYSTEMATIC_ZERO_FIELDS = {
    "Establised_Year",
    "Number_Doctor",
    "Num_Mediconsultant_or_Expert",
    "Total_Num_Beds",
    "Number_Private_Wards",
    "Num_Bed_for_Eco_Weaker_Sec",
}


def _review():
    return json.loads(REVIEW.read_text(encoding="utf-8"))


def test_nhd_field_semantics_review_is_fail_closed():
    review = _review()

    assert review["contract"] == "JLA_HEALTH_NHD_FIELD_SEMANTICS_REVIEW_V1"
    assert review["status"] == "authoritative_metadata_reviewed_semantics_unresolved"
    assert review["publication_allowed"] is False
    assert set(review["systematic_zero_fields_reviewed"]) == EXPECTED_SYSTEMATIC_ZERO_FIELDS

    findings = review["authoritative_metadata_findings"]
    assert findings["missing_token_semantics_defined"] is True
    assert set(findings["missing_tokens_supported_by_resource_metadata"]) == {"NA", "Blank"}
    assert findings["zero_semantics_defined"] is False
    assert findings["numeric_field_unit_definitions_found"] is False
    assert findings["systematic_zero_capacity_fields_explained"] is False
    assert findings["record_level_reference_period_defined"] is False
    assert findings["state_id_namespace_defined"] is False
    assert findings["district_id_namespace_defined"] is False


def test_nhd_systematic_zeros_cannot_be_reinterpreted_or_published():
    review = _review()
    conclusion = review["scientific_conclusion"]

    assert conclusion["authoritative_documentation_sufficient_to_interpret_observed_zero_as_true_absence"] is False
    assert conclusion["authoritative_documentation_sufficient_to_recode_zero_as_missing"] is False
    assert conclusion["indicator_eligibility_established"] is False

    action = conclusion["action"].lower()
    assert "preserve observed zeros" in action
    assert "preserve missing tokens as null" in action
    assert "excluded from indicators" in action
    assert "authoritative" in action


def test_nhd_geography_and_time_remain_source_native_until_evidenced():
    review = _review()
    geography = review["geography_conclusion"]
    temporal = review["temporal_conclusion"]

    assert geography["id_namespace_resolved"] is False
    assert geography["name_matching_authorized"] is False
    assert geography["crosswalk_authorized"] is False
    assert "source-native and uninterpreted" in geography["action"]
    assert "without independent authoritative evidence" in geography["action"]

    assert temporal["catalog_update_date_is_record_date"] is False
    assert temporal["monthly_granularity_establishes_row_reference_period"] is False
    assert temporal["time_labelled_indicator_authorized"] is False


def test_nhd_review_forbids_silent_source_value_rewrites():
    review = _review()
    rules = set(review["rules"])

    assert "Absence of an authoritative zero definition is not evidence that zero means missing." in rules
    assert "Absence of an authoritative zero definition is not evidence that zero means true absence." in rules
    assert "Observed source values are never silently rewritten to satisfy an indicator schema." in rules
    assert "This review does not authorize row-level publication or derived outputs." in rules
    assert "Module 2 remains IN DEVELOPMENT." in rules
