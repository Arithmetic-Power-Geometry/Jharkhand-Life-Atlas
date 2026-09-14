# Module 2 — Health & Healthcare Access

Status: **IN DEVELOPMENT — validated historical evidence published; current/differently dated official evidence remains fail-closed**.

This module builds a place-linked evidence layer for healthcare facilities, service capacity, quality certification, service activity and accessibility in Jharkhand. It depends on the completed Core Geography module and keeps Census 2011 health evidence separate from current administrative/facility systems unless a verified temporal/geographic linkage exists.

## Verified evidence already published

JLA now publishes a validated source-native Census 2011 Health extract derived only from the already-governed Module 1 village-amenities evidence:

- `data/curated/health_access/census_health_access_2011.csv`
- `data/curated/health_access/census_health_access_2011.provenance.json`
- `modules/health_access/RESEARCH_USE_CENSUS2011.md` — research-use, reproducibility and interpretation guidance
- **32,394 rows**
- **69 source-native health fields**
- reference year: **2011**
- derivation: direct field projection only
- no imputation, aggregation, recoding, current-geography substitution or derived availability claim
- missing source values remain missing/null and are never converted to zero
- source and output SHA-256 values are recorded in the provenance sidecar

The Streamlit Research page exposes this historical dataset only when its provenance sidecar reports `validated_source_native_historical_extract`. It is labelled explicitly as historical Census 2011 evidence and must not be interpreted as a current facility inventory.

## Current authoritative acquisition targets

The governed source inventory in `sources.yaml` includes official Census of India, Open Government Data Platform India / Ministry of Health and Family Welfare, NIHFW, National Health Authority, NHSRC / National Health Mission and CBHI sources. High-priority current or differently dated acquisition targets include:

- NIN Health Facilities with Geo Code and additional parameters
- National Hospital Directory with Geo Code and additional parameters
- All India Health Centres Directory
- Jharkhand HMIS district time series and the newer all-States/districts HMIS catalog
- NFHS-5 district factsheet evidence

Discovery metadata is never treated as acquired evidence. Exact authoritative payload acquisition, immutable evidence capture, retrieval metadata, hash/API provenance, observed-schema inspection, rights/attribution checks and temporal/geographic validation are required source by source before publication.

### National Hospital Directory evidence

JLA has now verified one explicit primary official `data.gov.in` National Hospital Directory payload against the governed candidate. The primary official payload and governed candidate match exactly at **10,341,256 bytes** with SHA-256:

`1ddcad9f9b922142a4374c7b89b70fb6cefd8a257448c70a61e1c07d98845134`

Durable non-publishing evidence is recorded in:

- `modules/health_access/evidence/nhd_primary_payload_binding_2026-09-14.json`
- `modules/health_access/evidence/nhd_jharkhand_aggregate_receipt_2026-09-13.json`
- `modules/health_access/evidence/nhd_authoritative_resource_identity_review_2026-09-14.json`
- `modules/health_access/evidence/nhd_numeric_quality_review_2026-09-14.json`
- `modules/health_access/evidence/nhd_temporal_metadata_review_2026-09-14.json`
- `modules/health_access/evidence/nhd_rights_review_2026-09-14.json`

This establishes byte-level identity for that **one explicit primary official payload only**. It does **not** establish deterministic canonical alias selection: the alternate official alias remains unresolved. It also does not establish row-level reference periods, administrative-vintage equivalence, semantic validity of the systematic-zero capacity fields, indicator eligibility, or publication readiness.

The aggregate receipt binds source hash, byte/row/column counts, successful CI evidence, privacy constraints, Jharkhand source-label row count, candidate-projection missingness counts and source-geography ambiguity audit. It contains no source rows or privacy-risk source values. Source `State_ID`/`District_ID` values remain uninterpreted and must not be treated as LGD, Census or current administrative identifiers without independently evidenced crosswalks.

The resource-specific rights review records that covered non-person facility fields may be considered for reuse under the Government Open Data License - India with required attribution, while personal information and named/contact fields remain excluded from publication. Rights review does not authorize publication by itself.

Six candidate numeric fields show a systematic-zero profile in the Jharkhand candidate and therefore remain **not indicator-eligible** pending authoritative field-semantic validation. Observed zero values are not silently changed to null, and missing values are never converted to zero.

ABDM Health Facility Registry remains restricted pending a reusable official export/API and acceptable terms. JLA does not scrape or republish person-level or otherwise unsupported records.

## Hard scientific and governance rules

No source means no published factual value. Discovery is not acquisition; acquisition is not publication. Missing is not zero. Person-level health records are excluded. District aggregates are never allocated to villages or facilities. Facility coordinates are not guessed. Public and private facility identities remain source-specific until deterministic or evidence-backed matching exists. Historical Census geography and current LGD/facility geography remain distinct unless an authoritative or otherwise defensible temporal crosswalk supports linkage. Similar names, dates or coordinates are never sufficient on their own to assert record equivalence.

## Completion sequence

1. Acquire exact authoritative reusable payloads for the priority current/differently dated sources.
2. Preserve immutable raw evidence or auditable API request provenance, retrieval time and SHA-256 where applicable.
3. Inspect observed schemas and preserve source identifiers, source labels, units, periods and suppression/missingness semantics.
4. Perform resource-specific licence/terms and attribution review.
5. Normalize facility type, ownership and service fields without erasing source-native values.
6. Link facilities/district observations to JLA geography only through verified codes, coordinates or evidence-backed temporal crosswalks; record match method and quality.
7. Build observed facility/capacity/service tables and derive indicators only where denominators, periods and geographic support are valid.
8. Add validation, tests, provenance, source-coverage updates, research-ready downloads/reports and Streamlit integration.
9. Require green CI on the exact `main` head before changing Module 2 status to COMPLETE.

## Completion boundary

The validated Census 2011 extract is a genuine published Health evidence layer and one primary official National Hospital Directory payload is now immutably byte-bound to its governed candidate. Neither fact by itself satisfies the full Module 2 completion gate. Module 2 remains **IN DEVELOPMENT** until remaining authoritative acquisition, privacy-safe row curation, semantic review, temporal interpretation, verified geographic linkage, valid indicators, validation, downloads/reports, Streamlit synchronization and green CI on the exact final `main` head are all verified.