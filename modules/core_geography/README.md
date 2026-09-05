# Core Geography & Census Baseline

This is the foundational Jharkhand Life Atlas module. Every future module connects to a stable `place_id`; place names alone are never treated as durable join keys.

## Scope

The final Module 1 target is a versioned geographic backbone for Jharkhand covering:

`State → District → Sub-district → Block → Gram Panchayat → Village/Town`

along with Census 2011 demographic baseline fields, official source crosswalks, temporal validity, provenance and quality metadata.

## Authoritative source set

The source inventory is defined in `sources.yaml` and `source_coverage.csv`. The core references are:

1. Census 2011 Location Code Directory (`PC11_TV_DIR`) for state/district/sub-district/village/town codes and names.
2. Jharkhand MDDS/PLCN rural directory (`PC11_MDDS_R-20`) for 2001↔2011 rural code crosswalks.
3. Village/Town-wise Primary Census Abstract 2011 for Jharkhand for households, population, age 0–6, SC/ST, literacy and worker counts.
4. Jharkhand District Census Handbooks for village/town directory amenities and PCA cross-checking.
5. Local Government Directory (LGD) for current district/block/panchayat/village relationships. Current LGD geography is kept separate from Census 2011 geography rather than silently back-projected.
6. Government of Jharkhand block references for official state-level cross-checking.

## Publication rules

- No source = no published factual value.
- Missing data ≠ zero.
- Census 2011 and current LGD records are different temporal views.
- No village, block or panchayat record may be fabricated from name lists or third-party mirrors.
- Third-party mirrors may help discover a source but are not accepted as the authoritative value source.
- Raw files are checksummed before transformation.
- Every curated row must carry `source_id`, `quality_class` and `record_status`.

## Current repository state

The public app currently contains the verified 24-district Census 2011 baseline. The ingestion engine in `ingest.py`, schema, source registry and validation framework are ready for the full official village/PCA/LGD inputs.

The authoritative catalogs have been verified, but the official Census raw workbooks could not be downloaded from the current execution environment. Therefore this module is deliberately **not falsely labelled complete** until the actual official files are ingested and row-level validation passes.

Run the official-file ingestion locally or in a network-enabled workflow, then execute:

```bash
python modules/core_geography/ingest.py village-directory data/raw/core_geography/Rdir_2001_MDDS_20.xls
python modules/core_geography/ingest.py pca data/raw/core_geography/<official-pca-file>.xlsx
python scripts/check.py
pytest -q
```

The resulting curated files can then be committed only after coverage, duplicate-code, hierarchy and provenance checks pass.
