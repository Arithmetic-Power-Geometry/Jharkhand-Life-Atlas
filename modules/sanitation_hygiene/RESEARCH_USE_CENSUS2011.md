# Research Use — Census 2011 Sanitation & Hygiene Extract

## Status and scope

This module publishes a **validated source-native historical extract** from the Jharkhand Census 2011 village amenities table. It documents source-native sanitation and drainage attributes for 2011; it is not evidence of present-day sanitation status.

- Dataset: `data/curated/sanitation_hygiene/census_sanitation_hygiene_2011.csv`
- Provenance: `data/curated/sanitation_hygiene/census_sanitation_hygiene_2011.provenance.json`
- Reference year: **2011**
- Rows: **32,394**
- Reviewed thematic fields: **11**
- Output SHA-256: `f8ebd0433426c76f5a8304049fb982f7408e1e8ab0440f9d0739682a50369e53`
- Source SHA-256: `d1e49a0ca337dedd6076e7071adce92574d0c48ae9e78b52c7cb7335424006c4`

The source-native fields cover drainage type/status, drainage discharge, Total Sanitation Campaign coverage, public community toilet-complex status and the recorded absence of a garbage-disposal system.

## Research-safe interpretation

Use the table only for analyses explicitly anchored to Census 2011 village geography and the meanings of the original fields. The extract is a direct reviewed projection: no imputation, aggregation, semantic recoding or present-day inference is applied by JLA.

Missing source values remain blank/null. They must not be converted to zero or interpreted as absence, failure, non-coverage or non-existence. Researchers should report missingness treatment and avoid changing denominators silently.

The field concerning drain-water discharge contains source-defined categories. Do not recode it into environmental-quality, pollution or treatment claims without a separately justified method and source evidence.

## Geography and temporal linkage

Rows remain on **Census 2011 source-native geography**. Never equate current LGD units with Census 2011 units because names happen to match. Cross-vintage linkage must use JLA's governed temporal crosswalk, preserve the relationship/evidence/vintage, and leave ambiguous or unresolved cases unresolved.

## Appropriate uses

Suitable uses include historical village-level descriptions of drainage/sanitation amenities, within-2011 spatial comparison, source missingness studies, and reproducible joint analysis with other Census-2011-native JLA extracts.

Do not present these fields as current SBM-G outcomes, current ODF/ODF Plus status, household toilet coverage, current solid/liquid-waste management, or current administrative truth. Contemporary SBM-G and related evidence remains a separate governed acquisition and validation stream.

## Reproducibility

The provenance JSON records the source/output hashes, selected fields, row and field counts, blank counts, source path and the explicit derivation/geography/missingness rules. Verify the output SHA-256 before analysis. The reproducible extraction path is `scripts/build_census2011_priority_extracts.py` with its CI workflow.

For publications, describe this artifact as a **Jharkhand Census 2011 source-native historical sanitation-and-hygiene extract**, cite the upstream Census source and the exact JLA repository/release, and follow `NOTICE.md`, source metadata and release-specific citation guidance.

## Completion boundary

This validated historical dataset is a substantial evidence asset but does **not** by itself make the full Sanitation & Hygiene module COMPLETE. Completion remains controlled by `modules/sanitation_hygiene/completion_gate.yaml` and requires every strict gate plus green CI on the exact final `main` head.
