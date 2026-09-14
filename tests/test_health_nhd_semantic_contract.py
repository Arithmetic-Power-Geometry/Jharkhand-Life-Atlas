import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "modules" / "health_access" / "national_hospital_directory_semantic_contract.json"
QUALITY = ROOT / "modules" / "health_access" / "evidence" / "nhd_numeric_quality_review_2026-09-14.json"


def load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def load_quality():
    return json.loads(QUALITY.read_text(encoding="utf-8"))


def test_nhd_semantic_contract_stays_nonpublishing_and_fail_closed():
    c = load_contract()
    assert c["contract"] == "JLA_HEALTH_NHD_SEMANTIC_CONTRACT_V2"
    assert c["publication_allowed"] is False
    assert c["row_level_curated_dataset_emitted"] is False
    assert c["indicator_rules"]["derived_outputs_publication_allowed"] is False


def test_missing_values_can_never_be_silently_zero_filled():
    c = load_contract()
    assert c["null_policy"]["canonical_missing_representation"] is None
    assert c["null_policy"]["missing_to_zero_allowed"] is False
    assert c["numeric_cleaning_rules"]["failed_parse_becomes_null"] is True
    assert c["numeric_cleaning_rules"]["zero_is_observed_value_only"] is True
    assert c["numeric_cleaning_rules"]["no_imputation"] is True
    assert c["numeric_cleaning_rules"]["no_cross_field_backfill"] is True


def test_systematic_zero_profiles_are_preserved_but_never_treated_as_validated_absence():
    c = load_contract()
    q = load_quality()
    rules = c["numeric_cleaning_rules"]
    assert rules["systematic_zero_profile_establishes_true_absence"] is False
    assert rules["systematic_zero_profile_establishes_field_validity"] is False
    assert rules["observed_zero_recode_to_null_allowed"] is False
    assert rules["systematic_zero_profile_requires_authoritative_semantic_validation"] is True
    assert c["indicator_rules"]["systematic_zero_profile_fields_indicator_eligible"] is False
    assert q["publication_allowed"] is False
    assert q["derived_indicator_use_allowed"] is False
    assert q["row_values_exported"] is False
    assert q["privacy_risk_values_exported"] is False
    assert q["interpretation_boundary"]["observed_zero_is_preserved_as_zero"] is True
    assert q["interpretation_boundary"]["observed_zero_may_be_reclassified_as_missing"] is False


def test_verified_numeric_profiles_remain_blocked_from_scientific_indicators():
    c = load_contract()
    q = load_quality()
    expected = set(c["field_groups"]["systematic_zero_profile_fields"])
    assert expected == set(q["numeric_field_profiles"])
    assert expected == {
        "Establised_Year", "Number_Doctor", "Num_Mediconsultant_or_Expert",
        "Total_Num_Beds", "Number_Private_Wards", "Num_Bed_for_Eco_Weaker_Sec"
    }
    for field, profile in q["numeric_field_profiles"].items():
        assert profile["jharkhand_rows"] == 478
        assert profile["observed_zero"] == profile["observed_nonmissing"]
        assert profile["nonzero_observed"] == 0
        assert profile["negative"] == 0
        assert profile["fractional"] == 0
        assert profile["unparsable"] == 0
        assert profile["status"] == "systematic_zero_profile_blocked"
    assert q["numeric_field_profiles"]["Total_Num_Beds"]["observed_nonmissing"] == 478
    assert q["numeric_field_profiles"]["Total_Num_Beds"]["governed_missing"] == 0
    for field in expected - {"Total_Num_Beds"}:
        assert q["numeric_field_profiles"][field]["observed_nonmissing"] == 475
        assert q["numeric_field_profiles"][field]["governed_missing"] == 3


def test_geography_and_temporal_semantics_remain_unresolved_until_evidenced():
    c = load_contract()
    assert set(c["field_groups"]["geography_identifiers_uninterpreted"]) == {"State_ID", "District_ID"}
    assert c["geography_rules"]["name_equality_establishes_equivalence"] is False
    assert c["geography_rules"]["normalization_establishes_equivalence"] is False
    assert c["geography_rules"]["authoritative_crosswalk_required"] is True
    assert c["geography_rules"]["administrative_vintage_required"] is True
    assert c["temporal_rules"]["resource_update_date_is_record_date"] is False
    assert c["temporal_rules"]["download_date_is_record_date"] is False
    assert c["temporal_rules"]["current_latest_claim_allowed"] is False


def test_rate_and_count_indicators_remain_blocked_before_scientific_linkage():
    c = load_contract()
    rules = c["indicator_rules"]
    assert rules["facility_counts_allowed_before_geography_resolution"] is False
    assert rules["district_rates_allowed_before_geography_resolution"] is False
    assert rules["bed_or_doctor_rates_allowed_without_valid_denominator_and_reference_period"] is False


def test_privacy_risk_fields_are_explicitly_excluded_from_semantic_curation():
    c = load_contract()
    excluded = set(c["field_groups"]["privacy_excluded"])
    for field in {
        "Telephone", "Mobile_Number", "Emergency_Num", "Ambulance_Phone_No",
        "Bloodbank_Phone_No", "Hospital_Primary_Email_Id", "Nodal_Person_Info"
    }:
        assert field in excluded
    numeric = set(c["field_groups"]["numeric_candidate_fields"])
    assert "Number_Doctor" in numeric
    assert "Total_Num_Beds" in numeric
    assert not (numeric & excluded)
