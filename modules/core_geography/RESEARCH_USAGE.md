# Module 1 research usage guide

This guide documents safe research use of the verified Core Geography backbone. It does not change any module publication status and does not assert unsupported historical/current geographic equivalence.

## Choose the temporal geography first

Use the Census 2011 view for analyses whose observations are tied to Census 2011 district, subdistrict, village, town, or ward codes. Use the current LGD view for observations whose source explicitly carries current LGD identifiers or whose geographic linkage has been independently verified against the appropriate LGD vintage.

Do not join Census 2011 villages directly to current LGD villages by normalized name. The verified release currently asserts zero official Census-2011-to-current-LGD village links because the retrieved LGD response does not expose a Census 2011 code field. Keep unmatched records unmatched until an authoritative relationship is available.

## Join discipline

1. Retain the source's original geographic identifier and geographic vintage.
2. Select the matching JLA temporal geography view.
3. Join on authoritative codes when the source provides them.
4. Where an evidence-backed crosswalk exists, retain relationship type and verification status with the joined record.
5. Treat split, merge, boundary-change, one-to-many, many-to-one, and unresolved relationships as explicit temporal events; never collapse them into simple equivalence.
6. Do not allocate district, block, or village aggregate values to finer units without an independently validated method and an explicitly derived-output contract.

## Missingness

Missing, unavailable, suppressed, not-applicable, and not-yet-linked values are not zero. Preserve nulls and source-specific missingness flags. A zero may be published only when the authoritative source actually reports a valid zero under the source's semantics.

## Provenance

Research outputs should retain, at minimum: source identifier, source authority, retrieval or source date, temporal geography/vintage, transformation version, and JLA release/commit identifier. Source-specific licence and attribution terms continue to apply.

## Reproducibility

Recompute statistics, tables, and figures from version-pinned curated artifacts and repository code. Do not manually transcribe manuscript values. Record the exact release commit/tag and verify green CI for that release before citing derived results as release outputs.

## Current verified scope

The Module 1 research-release manifest records 24 Census 2011 districts, 261 Census 2011 subdistricts, 32,624 Census 2011 villages, 24 current LGD districts, 264 current LGD subdistricts, 264 current blocks, 4,369 current panchayats, and 32,962 current LGD villages. These are separate temporal views, not a claim that every historical unit has a verified current equivalent.

## Citation

Use the repository `CITATION.cff` for project citation metadata. A dedicated dataset-paper DOI has not yet been minted; do not cite one until the release manifest records it as independently verified.
