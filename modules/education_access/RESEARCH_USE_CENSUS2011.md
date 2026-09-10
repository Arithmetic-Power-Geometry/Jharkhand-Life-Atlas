# Research Use — Census 2011 Education Access Extract

## Status and scope

This module publishes a **validated source-native historical extract** from the Jharkhand Census 2011 village amenities table. It records education-facility availability/count fields as represented in that source and vintage; it is not a current school registry.

- Dataset: `data/curated/education_access/census_education_access_2011.csv`
- Provenance: `data/curated/education_access/census_education_access_2011.provenance.json`
- Reference year: **2011**
- Rows: **32,394**
- Reviewed thematic fields: **40**
- Output SHA-256: `dd334056685e868fcdaa4d5c27c6d05f17bdbe4d2bae6f02781f5a22e26bf944`
- Source SHA-256: `d1e49a0ca337dedd6076e7071adce92574d0c48ae9e78b52c7cb7335424006c4`

The fields include government/private pre-primary, primary, middle, secondary and senior-secondary school status/counts; arts/science degree colleges; engineering and medicine colleges; vocational/ITI institutions; and schools for disabled persons, as represented in the Census source.

## Research-safe interpretation

Use these variables for analyses explicitly anchored to **Census 2011** and the original field meanings. JLA performs a direct reviewed field projection only: no imputation, aggregation, semantic recoding or current-status inference is introduced.

Missing source values remain blank/null and must not be silently converted to zero. A blank count is not evidence that a village had zero institutions. Researchers should disclose missing-value treatment and distinguish source-native status variables from source-native numeric count variables.

The dataset describes recorded amenities, not enrolment, attendance, learning outcomes, teacher availability, school quality, accessibility, recognition status or current operational status unless the original variable explicitly supports that interpretation.

## Geography and temporal linkage

Rows remain on **Census 2011 source-native geography**. Do not join them to current LGD villages, panchayats, blocks or districts by name equality alone. Cross-vintage use must go through JLA's governed temporal geography crosswalk and retain the relationship type, evidence, vintage and ambiguity; unmatched or uncertain units remain unresolved.

## Appropriate uses

Suitable uses include historical education-access description, within-2011 spatial comparison, government/private amenity comparisons where the source supports them, missingness analysis, and reproducible analysis with other Census-2011-native JLA datasets.

Do not represent this extract as current UDISE+ school-level truth, current school counts, current enrolment, current infrastructure or current administrative coverage. UDISE+ and other contemporary education evidence must pass separate acquisition, rights, observed-schema, geography and validation gates before publication.

## Reproducibility

The provenance JSON records source/output hashes, source path, row count, selected 40 fields, per-field blank counts and the explicit derivation, geography and missingness rules. Verify the dataset SHA-256 before analysis. The reproducible build path is `scripts/build_census2011_priority_extracts.py` and its corresponding CI workflow.

For publications, identify the artifact as a **Jharkhand Census 2011 source-native historical education-access extract**, cite the upstream Census source and the exact JLA repository/release, and follow `NOTICE.md`, source metadata and release-specific citation guidance.

## Completion boundary

This validated historical dataset does **not** make the complete Education Access module COMPLETE. Module completion remains governed by `modules/education_access/completion_gate.yaml` and requires every strict publication criterion plus green CI on the exact final `main` head.
