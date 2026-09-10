# Research Use — Census 2011 Water Access Extract

## Status and scope

This module publishes a **validated source-native historical extract** from the Jharkhand Census 2011 village amenities table. It is historical evidence, not a statement of current water-service availability.

- Dataset: `data/curated/water_access/census_water_access_2011.csv`
- Provenance: `data/curated/water_access/census_water_access_2011.provenance.json`
- Reference year: **2011**
- Rows: **32,394**
- Reviewed thematic fields: **27**
- Output SHA-256: `1dd9efb9557525946d53f8bfb855d916fb54e94d1eaf95ca7c69be3a0eb492e6`
- Source SHA-256: `d1e49a0ca337dedd6076e7071adce92574d0c48ae9e78b52c7cb7335424006c4`

The fields cover source-native status/functioning variables for treated and untreated tap water, covered and uncovered wells, hand pumps, tube wells/boreholes, springs, rivers/canals and tanks/ponds/lakes.

## Research-safe interpretation

Use the table for questions explicitly anchored to Census 2011 village geography and the meanings of the original source fields. The extract is a direct reviewed projection; JLA does not impute, aggregate, semantically recode, or infer current conditions from it.

Missing source values are preserved as blank/null representations. A blank is **not** evidence of absence, non-functionality, zero coverage, or zero facilities. Analyses must report their handling of missing values and should retain missingness in denominators unless a defensible source-specific rule is stated.

## Geography and temporal linkage

Rows remain on **Census 2011 source-native geography**. Do not join this dataset to current LGD villages, panchayats, blocks or districts by names alone. Any historical-to-current linkage must use JLA's governed temporal crosswalk service and retain the crosswalk evidence, relationship type, vintage and ambiguity. Unresolved or non-equivalent units must remain unresolved rather than being forced into a match.

## Appropriate uses

Suitable uses include reproducible historical descriptions of village water amenities, within-2011 spatial comparison, missingness analysis, source-functioning pattern analysis, and explicitly documented linkage to other Census-2011-native evidence.

Do not use this dataset as evidence of present-day Jal Jeevan Mission coverage, current tap functionality, current drinking-water quality, household-level service, or current administrative status. Current JJM and other contemporary evidence are governed separately and may only be published after their own acquisition, rights, schema, geography and validation gates pass.

## Reproducibility

The provenance JSON records the source file, source hash, output hash, selected fields, row count, field count, blank counts, geography rule, missing-value rule and derivation rule. Verify the dataset hash before analysis. The reproducible build is driven by `scripts/build_census2011_priority_extracts.py` and the corresponding CI workflow.

When publishing results, identify the dataset as a **Jharkhand Census 2011 source-native historical water-access extract** and cite the upstream Census source and the JLA repository/release used. Follow repository `NOTICE.md`, source metadata and any release-specific citation information.

## Completion boundary

Availability of this validated historical dataset does **not** make the full Water Access module COMPLETE. Module completion remains governed by `modules/water_access/completion_gate.yaml` and requires every publication criterion plus green CI on the exact final `main` head.
