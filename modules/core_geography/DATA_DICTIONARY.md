# Module 1 — Core Geography Data Dictionary

This data dictionary documents the stable production fields for the Jharkhand Life Atlas core geography layer. It is intended for the Module 1 scientific dataset/research release and must be read together with the module schema, source registry, governance policy, and release manifest.

## Core place fields

| Field | Type | Required | Meaning | Null semantics |
|---|---|---:|---|---|
| `place_id` | string | yes | JLA-stable identifier for one geography record in the published core layer. | Must not be null; unique in the layer. |
| `place_type` | string | yes | Administrative/geographic level represented by the record, such as state, district, subdistrict, block, panchayat, or village. | Must not be null. |
| `name` | string | yes | Source-preserved or source-normalized place name used for display and audit. | Must not be null. Name equality alone never establishes temporal geographic equivalence. |
| `parent_place_id` | string | no | JLA identifier of the immediate parent geography when the hierarchy is supported by the source view. | Null means no supported parent link is asserted in that row; it does not mean the place has no administrative parent in reality. |
| `state_code` | string | yes | Source-era state identifier retained as a string to preserve leading zeros and source semantics. | Must not be null. |
| `district_code` | string | no | Source-era district identifier when available for the represented place. | Null means unavailable/not applicable in that source view; never convert to `0`. |
| `subdistrict_code` | string | no | Source-era subdistrict identifier when available. | Null means unavailable/not applicable; never infer from names. |
| `block_code` | string | no | Source-era block identifier when available. | Null means unavailable/not applicable. Historical and current block codes are not silently merged. |
| `panchayat_code` | string | no | Source-era panchayat/local-body identifier when available. | Null means unavailable/not applicable. |
| `village_code` | string | no | Source-era village identifier when available. | Null means unavailable/not applicable. Census and current LGD village identifiers remain distinct unless an evidence-backed crosswalk supports linkage. |
| `latitude` | float | no | Latitude supplied or lawfully derived from an explicitly documented authoritative source. | Null means no validated coordinate is available; never substitute a centroid or zero without an explicit documented method. |
| `longitude` | float | no | Longitude supplied or lawfully derived from an explicitly documented authoritative source. | Null means no validated coordinate is available; never substitute a centroid or zero without an explicit documented method. |
| `source_id` | string | yes | Identifier linking the row to the JLA source registry/provenance record. | Must not be null. |
| `quality_class` | string | yes | JLA quality/provenance classification for the row, determined by the ingestion and validation workflow. | Must not be null; it is not a subjective score and must not be used to hide unresolved provenance. |

## Temporal geography rules

Module 1 intentionally preserves multiple geographic vintages. Census-2011 geography and current Local Government Directory geography are separate source views. A matching name is never sufficient evidence that two historical/current administrative units are the same unit.

A temporal crosswalk may assert a direct link only when authoritative evidence supports the relationship. Split, merge, boundary-change, renamed-with-boundary-change, or unresolved relationships remain explicit and must not be collapsed into one-to-one equivalence. Unsupported links remain null/unmatched.

## Missing-value rules

Missing, unavailable, not-applicable, unresolved, and suppressed observations must remain distinguishable from measured zero. JLA does not convert missing administrative codes, coordinates, amenities, counts, or linkage fields to zero merely to simplify analysis.

## Provenance and licensing

Every published row must retain a `source_id` that resolves to JLA provenance metadata. Third-party source licensing and attribution remain separate from the JLA software licence. Researchers redistributing derived datasets must observe the source-specific terms recorded in the repository.

## Release-use note

Manuscript tables, figures, counts, and examples for the Module 1 dataset paper must be regenerated from version-pinned release artifacts. This document defines field meaning; it does not authorize publication of any artifact whose source-specific redistribution or release gate has not been verified.
