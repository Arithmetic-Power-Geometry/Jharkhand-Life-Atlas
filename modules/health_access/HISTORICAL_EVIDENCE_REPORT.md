# Health & Healthcare Access — Validated Historical Evidence Report

## Scope

This report summarizes only the validated **Census 2011 source-native Health evidence** currently admitted to Jharkhand Life Atlas (JLA) Module 2. It is a research-ready description of committed evidence, not a statement of present-day health-facility availability.

## Validated dataset

- Module: `health_access`
- Reference year: **2011**
- Geography: **Census 2011 source-native village geography**
- Curated dataset: `data/curated/health_access/census_health_access_2011.csv`
- Provenance: `data/curated/health_access/census_health_access_2011.provenance.json`
- Rows: **32,394**
- Reviewed Health fields: **69**
- Curated output SHA-256: `bde8777dd7148d84f0107bb48cac995f7fd691599cb760238975843c0a2c1292`
- Upstream curated Census amenities SHA-256: `d1e49a0ca337dedd6076e7071adce92574d0c48ae9e78b52c7cb7335424006c4`
- Validation state: `validated_source_native_historical_extract`

## Derivation contract

The dataset is a **direct field projection only**. JLA does not impute, aggregate, recode, or manufacture derived availability claims in this historical extract. Missing source values remain null/blank representations and are never silently converted to zero.

The dataset remains on its **2011 Census geography**. A current LGD district, block, gram panchayat or village name must not be treated as equivalent to a Census 2011 unit merely because the names look the same. Any cross-vintage linkage requires explicit evidence in the shared geography-crosswalk service.

## Missingness audit

The committed provenance contains per-field blank counts for every admitted Health field. These counts are evidence about source completeness, not zeros and not evidence of facility absence. Several facility/staff fields have roughly three thousand blank source records, while some distance-to-nearest-facility fields have substantially more. Researchers must therefore distinguish `missing/blank` from numeric `0` and from coded distance categories.

## Interpretation limits

This historical evidence can support research about **2011 village-level recorded health amenities and source-native facility/staff variables**. It must not be used to claim current facility existence, current staffing, present service quality, current catchment accessibility, or current administrative placement.

Current and differently dated evidence streams—including the preferred 2026 OGD facility resources, HMIS, NFHS-5 and other official Health sources—remain governed independently. They require authoritative payload acquisition, immutable retrieval evidence, hashes, observed-schema inspection, explicit Jharkhand filtering, temporal/geographic validation and publication-gate approval before JLA can publish them.

## Reproducibility and citation

Any analysis using this file should report the reference year (2011), the JLA dataset path, the output SHA-256 above, the upstream source SHA-256 above, and the restriction that the extract is source-native historical evidence. Analyses should preserve missing values and should not silently join the dataset to current administrative geography.

## Publication state

**Validated historical evidence available; Module 2 remains IN DEVELOPMENT.**

Module 2 may become `COMPLETE` only after every criterion in `modules/health_access/completion_gate.yaml` is satisfied and CI is green on the exact final `main` head.