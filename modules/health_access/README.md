# Module 2 — Health & Healthcare Access

Status: **IN DEVELOPMENT — validated historical evidence published; current/differently dated official evidence remains fail-closed**.

This module builds a place-linked evidence layer for healthcare facilities, service capacity, quality certification, service activity and accessibility in Jharkhand. It depends on the completed Core Geography module and keeps Census 2011 health evidence separate from current administrative/facility systems unless a verified temporal/geographic linkage exists.

## Verified evidence already published

JLA now publishes a validated source-native Census 2011 Health extract derived only from the already-governed Module 1 village-amenities evidence:

- `data/curated/health_access/census_health_access_2011.csv`
- `data/curated/health_access/census_health_access_2011.provenance.json`
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

These resources are not treated as acquired merely because their official catalog/resource pages have been verified. Exact authoritative payload acquisition, immutable evidence capture, retrieval metadata, hash/API provenance, observed-schema inspection, rights/attribution checks and temporal/geographic validation are still required before publication.

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

The validated Census 2011 extract is a genuine published Health evidence layer, but it does **not** by itself satisfy the full Module 2 completion gate. Module 2 remains **IN DEVELOPMENT** until current/differently dated authoritative acquisition, rights review, provenance, geographic linkage, indicators, validation, downloads/reports, Streamlit synchronization and green CI on `main` are all verified.
