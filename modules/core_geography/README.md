# Core Geography & Census Baseline

Module 1 is the foundational Jharkhand Life Atlas (JLA) research layer. Every later module connects to a stable `place_id`; place names alone are never treated as durable join keys.

## Status

**Version 1.2.0 — COMPLETE / research-ready.**

The authoritative sync and completion pipeline has passed its publication gate. The verified statewide release contains:

- Census 2011 geographic backbone: **1 state, 24 districts, 261 subdistricts and 32,624 villages**.
- Primary Census Abstract baseline: **32,623 whole-place rows from 24 Jharkhand district workbooks**, with 8 core demographic fields populated.
- Current LGD view: **24 districts, 264 subdistricts, 264 blocks, 4,369 panchayats and 32,962 villages**.
- DCHB village amenities: **32,394 Census-verified village rows** and 394 populated source fields.
- MDDS 2001↔2011 evidence: **32,584 verified 2011 village rows**, of which **32,583 carry an explicit 2001 source code**.
- Census 2011↔current LGD temporal view: all **32,624 Census villages retained explicitly**; **no village-level official links are asserted** because the retrieved LGD response does not expose a Census-2011 village-code field.

The machine-readable audit is `sync_report.json`. It records source URLs, checksums, row counts, validation results and completion-layer status.

## Scope

The module supplies a versioned geographic backbone for Jharkhand across the research hierarchy:

`State → District → Subdistrict → Block → Gram Panchayat → Village/Town`

The hierarchy is deliberately temporal. Census 2001/2011 evidence and contemporary LGD administration are not silently collapsed into one geography.

## Authoritative source set

The authoritative inventory is defined in `sources.yaml`, `source_coverage.csv` and the repository-wide `registry/sources.csv`. Core sources are:

1. Census 2011 Location Code Directory (`PC11_TV_DIR`) for state, district, subdistrict, village and town codes and names.
2. Jharkhand MDDS/PLCN rural directory (`PC11_MDDS_R-20`) for explicit 2001↔2011 rural code evidence.
3. Village/Town-wise Primary Census Abstract 2011 for Jharkhand for demographic baseline fields.
4. Jharkhand District Census Handbook village/town directory release for amenities and supporting Census evidence.
5. Local Government Directory (LGD) for the current administrative view of districts, subdistricts, blocks, panchayats and villages.
6. Government of Jharkhand block references for official state-level cross-checking where appropriate.

## Publication and research rules

- **No source = no published factual value.**
- **Missing data ≠ zero.**
- Census 2011 and current LGD records are separate temporal views.
- No village, block, panchayat or temporal match is fabricated from name similarity.
- Third-party mirrors may assist discovery but are not accepted as authoritative value sources.
- Retrieved official files are checksummed before transformation where file acquisition applies.
- Curated evidence preserves source/provenance and quality metadata.
- Unsupported Census↔LGD village matches remain explicitly unmatched.

## Reproducibility

The authoritative pipeline is implemented in `sync_official.py`, `sync_runner.py`, `sync_fast_runner.py` and the hardened completion runner `complete_module1_v2.py`. GitHub Actions executes the sync/validation workflow, while repository tests and `scripts/check.py` provide additional contract checks.

Researchers should use the curated files under `data/curated/core_geography/` rather than reinterpreting raw filenames or joining temporal geographies by names. For publication or downstream analysis, cite JLA and the underlying authoritative sources used by the extract.
