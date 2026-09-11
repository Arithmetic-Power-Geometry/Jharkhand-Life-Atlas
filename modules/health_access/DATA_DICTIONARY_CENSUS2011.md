# Module 2 Census 2011 Health Evidence Data Dictionary

## Scope and publication state

This dictionary documents the governed historical dataset at `data/curated/health_access/census_health_access_2011.csv`.

- Module: Health & Healthcare Access (`health_access`)
- Reference year: 2011
- Geography vintage: Census 2011
- Geography level: village/source-native Census geography
- Rows: 32,394
- Health evidence fields: 69
- Publication state: `validated_source_native_historical_extract`
- Derivation: direct field projection from the governed Census-2011 village-amenities table only

This is historical evidence. It is **not** a current facility inventory, does not establish current service availability, and must not be joined to current LGD places by name equality alone.

## Provenance and reproducibility

The governed provenance record is `data/curated/health_access/census_health_access_2011.provenance.json`.

- Source: `data/curated/core_geography/village_amenities_2011.csv`
- Source SHA-256: `d1e49a0ca337dedd6076e7071adce92574d0c48ae9e78b52c7cb7335424006c4`
- Curated output SHA-256: `bde8777dd7148d84f0107bb48cac995f7fd691599cb760238975843c0a2c1292`
- Builder: `modules/health_access/build_census2011_health_extract.py`

Missing source values are preserved as empty/null representation and are **never converted to zero**. The builder performs no imputation, aggregation, semantic recoding, present-day inference, or current-geography remapping.

## Identity and geography fields

| Field | Meaning / handling |
|---|---|
| `state_code` | Source-native Census state code |
| `state_name` | Source-native state name |
| `district_code` | Source-native Census district code |
| `district_name` | Source-native Census district name |
| `sub_district_code` | Source-native Census sub-district code |
| `sub_district_name` | Source-native Census sub-district name |
| `village_code` | Source-native Census village code |
| `village_name` | Source-native Census village name |
| `cd_block_code` | Source-native CD-block code where present |
| `cd_block_name` | Source-native CD-block name where present |
| `gram_panchayat_code` | Source-native Gram Panchayat code where present |
| `gram_panchayat_name` | Source-native Gram Panchayat name where present |
| `reference_year` | Must be `2011` for this release |

Additional `source_*` or `jla_*` fields may be carried through by the builder as provenance fields. Their presence does not authorize geographic equivalence outside the source vintage.

## Government/public health-facility field families

For each facility family below, the five quantitative source-native fields are retained exactly as supplied: facility number, doctors total strength, doctors in position, para-medical staff total strength, and para-medical staff in position. A sixth field retains the source-native coded distance range to the nearest place where the facility is available when it is not available within the village. JLA does not recode the distance value in this historical extract.

### Community Health Centre

- `community_health_centre_numbers`
- `community_health_centre_doctors_total_strength_numbers`
- `community_health_centre_doctors_in_position_numbers`
- `community_health_centre_para_medical_staff_total_strength_numbers`
- `community_health_centre_para_medical_staff_in_position_numbers`
- `if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_15`

### Primary Health Centre

- `primary_health_centre_numbers`
- `primary_health_centre_doctors_total_strength_numbers`
- `primary_health_centre_doctors_in_position_numbers`
- `primary_health_centre_para_medical_staff_total_strength_numbers`
- `primary_health_centre_para_medical_staff_in_position_numbers`
- `if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_16`

### Primary Health Sub-Centre

Historical source spelling is preserved in the machine fields.

- `primary_heallth_sub_centre_numbers`
- `primary_heallth_sub_centre_doctors_total_strength_numbers`
- `primary_heallth_sub_centre_doctors_in_position_numbers`
- `primary_heallth_sub_centre_para_medical_staff_total_strength_numbers`
- `primary_heallth_sub_centre_para_medical_staff_in_position_numbers`
- `if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_17`

### Maternity and Child Welfare Centre

- `maternity_and_child_welfare_centre_numbers`
- `maternity_and_child_welfare_centre_doctors_total_strength_numbers`
- `maternity_and_child_welfare_centre_doctors_in_position_numbers`
- `maternity_and_child_welfare_centre_para_medical_staff_total_strength_numbers`
- `maternity_and_child_welfare_centre_para_medical_staff_in_position_numbers`
- `if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_18`

### TB Clinic

- `tb_clinic_numbers`
- `tb_clinic_doctors_total_strength_numbers`
- `tb_clinic_doctors_in_position_numbers`
- `tb_clinic_para_medical_para_medical_staff_total_strength_numbers`
- `tb_clinic_para_medical_para_medical_staff_in_position_numbers`
- `if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_19`

### Allopathic Hospital

- `hospital_allopathic_numbers`
- `hospital_allopathic_doctors_total_strength_numbers`
- `hospital_allopathic_doctors_in_position_numbers`
- `hospital_allopathic_para_medical_staff_total_strength_numbers`
- `hospital_allopathic_para_medical_staff_in_position_numbers`
- `if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_20`

### Alternative-Medicine Hospital

Historical source spelling is preserved in the machine fields.

- `hospiltal_alternative_medicine_numbers`
- `hospiltal_alternative_medicine_doctors_total_strength_numbers`
- `hospiltal_alternative_medicine_doctors_in_position_numbers`
- `hospiltal_alternative_medicine_para_medical_staff_total_strength_numbers`
- `hospiltal_alternative_medicine_para_medical_staff_in_position_numbers`
- `if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_21`

### Dispensary

- `dispensary_numbers`
- `dispensary_doctors_total_strength_numbers`
- `dispensary_doctors_in_position_numbers`
- `dispensary_para_medical_staff_total_strength_numbers`
- `dispensary_para_medical_staff_in_position_numbers`
- `if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_22`

### Mobile Health Clinic

- `mobile_health_clinic_numbers`
- `mobile_health_clinic_doctors_total_strength_numbers`
- `mobile_health_clinic_doctors_in_position_numbers`
- `mobile_health_clinic_para_medical_staff_total_strength_numbers`
- `mobile_health_clinic_para_medical_staff_in_position_numbers`
- `if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_24`

### Family Welfare Centre

- `family_welfare_centre_numbers`
- `family_welfare_centre_doctors_total_strength_numbers`
- `family_welfare_centre_doctors_in_position_numbers`
- `family_welfare_centre_para_medical_staff_total_strength_numbers`
- `family_welfare_centre_para_medical_staff_in_position_numbers`
- `if_not_available_within_the_village_the_distance_range_code_of_nearest_place_where_facility_is_available_is_given_viz_a_for_5_kms_b_for_5_10_kms_and_c_for_10_kms_25`

## Non-government medical-facility fields

These are retained as source-native historical count/evidence fields; JLA does not reinterpret blanks as zero or infer current provider availability.

- `non_government_medical_facilities_out_patient_numbers`
- `non_government_medical_facilities_in_and_out_patient_numbers`
- `non_government_medical_facilities_charitable_numbers`
- `non_government_medical_facilities_medical_prctitioner_with_mbbs_degree_numbers`
- `non_government_medical_facilities_medical_prctitioner_with_other_degree_numbers`
- `non_government_medical_facilities_medical_practitioner_with_no_degree_numbers`
- `non_government_medical_facilities_traditional_practitioner_and_faith_healer_numbers`
- `non_government_medical_facilities_medicine_shop_numbers`
- `non_government_medical_facilities_others_numbers`

## Interpretation rules

1. A numeric value is interpreted only within the Census-2011 source definition represented by its field name; it is not evidence of current availability.
2. Blank/null is unknown/not supplied under the source representation and is never converted to zero.
3. Coded distance fields remain source-native. Do not silently transform them into continuous kilometres.
4. Census-2011 identifiers remain Census-2011 identifiers. Any linkage to another administrative vintage must use an evidence-backed temporal crosswalk and preserve linkage status/uncertainty; names alone are insufficient.
5. Staff-position and staff-strength fields must not be converted into staffing ratios unless the denominator is non-missing, semantically valid, and the resulting indicator is separately validated and documented.
6. The historical release contains no person-level health records and must not be extended with sensitive person-level data.
7. Source spelling is preserved where it forms part of the governed machine schema; user-facing labels may correct spelling only if the mapping remains explicit and lossless.
