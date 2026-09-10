# Research-use note — Health & Healthcare Access, Census 2011

## Scope

This note documents the validated historical Health evidence currently published by Jharkhand Life Atlas (JLA). It applies only to:

- `data/curated/health_access/census_health_access_2011.csv`
- `data/curated/health_access/census_health_access_2011.provenance.json`

The dataset contains **32,394 Jharkhand Census-2011 village rows** and **69 source-native health fields**. It is a direct projection from the governed Module 1 Census village-amenities table. It is historical evidence for reference year 2011 and must not be interpreted as a current facility inventory.

## Reproducibility and integrity

The provenance sidecar records:

- source: `data/curated/core_geography/village_amenities_2011.csv`
- source SHA-256: `d1e49a0ca337dedd6076e7071adce92574d0c48ae9e78b52c7cb7335424006c4`
- output SHA-256: `bde8777dd7148d84f0107bb48cac995f7fd691599cb760238975843c0a2c1292`
- row count: `32394`
- health field count: `69`
- status: `validated_source_native_historical_extract`

The build rule is direct field projection only. No imputation, aggregation, recoding, current-geography substitution or derived availability claim is introduced by this extract.

## Missingness

Blank/null source values are preserved as blank/null representations. They must never be silently converted to zero. A zero, where present in a source-native numeric field, is distinct from a missing value.

Researchers should inspect the provenance sidecar before analysis because field-specific blank counts are recorded there. Analyses that require complete cases should declare their filtering rule explicitly and should not treat omitted records as negative observations.

## Geography and time

All observations remain on **Census 2011 source-native geography**. JLA does not infer equivalence between Census 2011 villages/districts and current LGD or other administrative vintages from names alone.

Any longitudinal or current comparison must use an evidence-backed temporal/geographic crosswalk and must preserve the match method and uncertainty. Without such evidence, results should remain vintage-specific.

## Appropriate research uses

This extract is suitable for reproducible descriptive work on the historical distribution of source-recorded health amenities and related Census-2011 health fields, including village-level profiling, district-level summaries created from source-native 2011 geography, missingness analysis, and comparison with other Census-2011 JLA modules at compatible geography and vintage.

## Uses that are not supported

Do not use this dataset by itself to claim current healthcare availability, current facility counts, current staffing, current service quality, present-day accessibility, current district/village administrative membership, or causal effects. Do not allocate later district-level HMIS/NFHS statistics to villages or facilities. Do not combine current facility records with Census-2011 records merely because names are similar.

## Citation and provenance practice

A research output using this extract should cite JLA, identify the dataset path and reference year, state that the extract is a direct source-native projection of governed Census-2011 village amenities, and retain the provenance sidecar with any redistributed analytical package where permitted.

For exact reproducibility, record the JLA Git commit used, the output SHA-256 above, the analysis code version, any row/field filters, any crosswalk version, and all derived variable definitions.

## Publication boundary

This note does not change Module 2 status. Health & Healthcare Access remains **IN DEVELOPMENT** until the remaining authoritative current/differently dated health sources pass governed acquisition, rights review, observed-schema inspection, temporal/geographic linkage, indicator validation, reporting and exact-head green CI. No unsupported current-health output is authorized by this document.
