# Module 1 manuscript support

This note supports preparation of a dataset paper for the verified `core_geography` release. It is not evidence of journal submission, acceptance, publication, peer review, or DOI registration.

## Reproducible manuscript inputs

Generate all descriptive statistics, tables, and figure inputs from the curated repository artifacts rather than transcribing values manually:

```bash
python modules/core_geography/research_stats.py
python modules/core_geography/research_assets.py --output-dir outputs/research/core_geography
```

The asset generator writes:

- `manuscript_statistics.json`
- `table_descriptive_statistics.csv`
- `figure_geography_counts_long.csv`
- `asset_semantics.json`

The generated values are descriptive only. Missing values remain missing, no person-level data are used, and no cross-vintage administrative equivalence is inferred.

## Recommended paper structure

1. **Data context and motivation** — explain why Jharkhand requires a reproducible geography backbone before thematic village-level modules can be linked safely.
2. **Authoritative source families** — describe Census 2011 geography and village tables, current LGD administrative geography, DCHB village amenities, and the MDDS 2001–2011 crosswalk with source-specific provenance and licensing.
3. **Processing and validation** — document code preservation, null semantics, exact membership checks, deterministic ingestion, and repository tests.
4. **Temporal geography** — keep Census 2011 and current LGD as distinct vintages. The current release retains 32,624 Census 2011 villages and 32,962 current LGD villages, but those counts must not be interpreted as a one-to-one continuity series. The present Census–LGD temporal crosswalk asserts zero official village links because the retrieved LGD evidence does not expose a Census 2011 village-code field.
5. **Data records** — use `DATA_DICTIONARY.md` as the field-level reference and report only statistics regenerated from the pinned release artifacts.
6. **Technical validation** — summarize validation scripts/tests, deterministic manuscript-asset generation, provenance checks, and exact-release CI.
7. **Usage notes and limitations** — use `RESEARCH_USAGE.md`; explicitly warn against name-only joins or allocation of higher-level aggregates to villages.
8. **Availability and citation** — cite the repository/version and `CITATION.cff`. Add a dataset-release DOI only after a frozen, independently verified archival release is minted.

## Figure and table semantics

`table_descriptive_statistics.csv` is the canonical manuscript table input for release counts. `figure_geography_counts_long.csv` is the canonical long-form geography-count input. Figures must display `census_2011` and `current_lgd` as separate vintages or panels and must not visually imply entity-level continuity unless an independently verified crosswalk supports it.

## Reproducibility checklist before submission

- Pin the exact repository commit/tag used by the manuscript.
- Regenerate manuscript statistics and assets from that exact checkout.
- Confirm regenerated assets match the archived release copy byte-for-byte where applicable.
- Run the complete test suite and all Module 1 validation on the exact release head.
- Verify the data dictionary and usage guide still match the production schema.
- Preserve source-specific attribution and licence terms; archive only redistributable artifacts.
- Record unresolved temporal links as unmatched/null rather than filling them from names.
- Verify the manuscript makes no unsupported submission, publication, DOI, or cross-vintage equivalence claim.

## Current release-readiness boundary

The scientific dataset is marked complete at the module level, and reproducible manuscript-supporting statistics and figure/table inputs are available. Dataset-paper release preparation remains open until an exact release commit/tag has a recorded clean reproducibility run, redistributable archival package, final citation metadata, and—only after freezing and verification—a minted/registered DOI if one is desired.
