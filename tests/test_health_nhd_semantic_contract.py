import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "modules" / "health_access" / "national_hospital_directory_semantic_contract.json"


def load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_nhd_semantic_contract_stays_nonpublishing_and_fail_closed():
    c = load_contract()
    assert c["contract"] == "JLA_HEALTH_NHD_SEMANTIC_CONTRACT_V1"
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
