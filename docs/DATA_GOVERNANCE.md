# Jharkhand Life Atlas — Data Governance, Rights and Responsible Publication Policy

**Version 1.0 · 2026**  
**Project:** Jharkhand Life Atlas (JLA)  
**Principle:** *Measure conditions, not politicians. Publish evidence, not exposure.*

## 1. Purpose

Jharkhand Life Atlas is an independent, non-partisan public-interest research infrastructure. It connects geography, public-service conditions, environmental exposure, accessibility, risk and other evidence at the smallest defensible geographic level supported by authoritative data.

JLA is not a government portal and does not imply endorsement by any ministry, department, local body, institution, elected representative or data provider.

This policy governs whether a source may be acquired, transformed, linked, visualised, downloaded or republished by JLA. A dataset is not publishable merely because it is publicly visible on the internet.

## 2. Mandatory publication gate

Every source must pass all of the following checks before factual values derived from it are published:

1. **Authority** — publisher and responsible organisation are identified.
2. **Provenance** — source URL/catalogue identifier, reference period and retrieval method are recorded.
3. **Rights** — licence, terms of use or reuse policy is reviewed at resource level where possible.
4. **Attribution** — required credit statement is known and preserved.
5. **Privacy** — the source is checked for personal or re-identifiable information.
6. **Sensitivity** — wildlife, security, health, vulnerable-community and other disclosure risks are assessed.
7. **Geographic disclosure** — publication precision is no finer than is justified and safe.
8. **Scientific integrity** — observed, derived and modelled values are explicitly separated.
9. **Temporal integrity** — historical and current administrative geographies are not silently merged.
10. **Validation** — structural checks, missingness rules and module-specific tests pass.

**Hard rule: No source = no published factual value.**

## 3. Publication classes

Each source is assigned one publication class.

| Class | Meaning | JLA action |
|---|---|---|
| `OPEN` | Explicit open licence permits redistribution and reuse | Raw/structured publication may be allowed with required attribution |
| `OPEN_WITH_ATTRIBUTION` | Reuse is permitted subject to acknowledgement or other stated conditions | Publish only while preserving those conditions |
| `DERIVED_ONLY` | Source may be consulted/analysed but raw redistribution rights are not sufficiently clear | Publish only defensible derived facts/metadata where lawful; do not mirror the source file |
| `AGGREGATE_ONLY` | Person-level or sensitive detail exists but aggregate publication is defensible | Publish only approved aggregation/generalisation |
| `RESTRICTED` | Access or reuse is restricted, contractual, confidential or otherwise limited | Do not publish raw records; use only within the stated permission |
| `DO_NOT_PUBLISH` | Rights, privacy, safety or integrity risk is unacceptable | Exclude from public JLA outputs |

Unclear rights default to the more conservative class until verified.

## 4. Privacy and personal data

JLA is designed as a place-centred, not person-centred, atlas. Public releases must not contain directly identifying personal data unless a specific lawful, necessary and ethically justified publication basis has been reviewed separately.

The default public rule is:

- no names of private individuals tied to sensitive events;
- no phone numbers, email addresses, identity numbers or household-level identifiers;
- no individual medical records;
- no identifiable beneficiary, victim or compensation-claim records;
- no precise household coordinates where re-identification is plausible;
- no inference of sensitive attributes about identifiable people.

Where a source contains person-level information, JLA should prefer aggregation, suppression, generalisation or exclusion. Missing values must never be converted to zero to make aggregation easier.

## 5. Wildlife and environmental sensitivity

Human–elephant conflict and biodiversity modules are legitimate public-interest research topics, but publication must not create avoidable ecological or safety risk.

JLA may publish verified historical conflict patterns, affected administrative areas, seasonality, aggregated incidents, damage/compensation statistics, landscape context and access to services when rights and privacy checks permit.

JLA must not publish operationally sensitive information such as real-time or near-real-time locations of protected wildlife, den/nest locations, routes or other precision that could facilitate poaching, harassment or disturbance. Sensitive coordinates should be withheld, coarsened or delayed.

## 6. Government and open-data sources

Data published on the Government of India Open Government Data Platform are generally governed by the Government Open Data License - India at platform level, subject to the individual resource and exclusions. JLA must preserve attribution and must not imply government endorsement.

Government websites that are not covered by an explicit open-data licence are not automatically treated as unrestricted open data. Their terms/copyright policy must be recorded in the source registry.

For Census of India material, JLA must preserve accurate reproduction and prominent acknowledgement and must respect resource-specific copyright/reproduction conditions and third-party rights. Where raw redistribution permission is unclear, JLA uses a conservative `DERIVED_ONLY` posture rather than silently mirroring source files.

## 7. Research integrity

Every publishable observation must be classed as one of:

- **Observed** — directly reported by an identified source;
- **Derived** — calculated from observed values by a documented deterministic method;
- **Modelled** — estimated or predicted using an explicit model and uncertainty statement.

Derived indicators must retain their input source IDs, reference periods, method/version and quality status. Model outputs must never be presented as observed facts.

## 8. Geography and time

JLA preserves historical and current administrative systems as separate temporal views. Census 2011 codes, LGD current codes and later boundary structures may refer to different entities even when names match.

Crosswalks require evidence-backed codes or documented matching methods. Ambiguous matches remain unmatched. Name similarity alone is not sufficient for publication as an identity link.

## 9. Problem and vulnerability modules

JLA may study difficult public-interest conditions including human–elephant conflict, snakebite, vector-borne disease, drought, flood, heat, food security, migration, employment, mining/industrial environment and service-access gaps.

These modules describe **conditions and evidence**, not political responsibility. JLA does not score parties, elected representatives or governments and does not infer blame from spatial association.

A vulnerability or accessibility score must publish its formula, components, reference period, missing-data treatment and limitations. Rankings should be avoided where they create false precision or stigma; where comparative indicators are useful, they must be framed as data-defined conditions rather than judgments about communities.

## 10. Sensitive communities and small cells

For tribal communities, children, patients, victims, migrants and other potentially vulnerable groups, JLA applies heightened disclosure review. Small-cell counts or combinations of attributes that could make individuals identifiable should be suppressed, grouped or withheld.

## 11. Source registry requirements

Every `registry/sources.csv` record must include:

- `source_id`
- title, publisher and responsible department
- canonical source URL
- reference year/period
- geographic resolution
- licence or policy statement
- retrieval method
- citation key
- redistribution status
- publication class
- licence-review status
- personal-data risk
- sensitivity risk
- attribution requirement
- governance review status

Automated validation rejects missing governance fields or invalid publication classes.

## 12. Corrections and source changes

Source terms, administrative structures and official datasets can change. JLA should record retrieval dates/hashes where feasible, preserve reproducibility, and correct or withdraw records when a source, licence, privacy assessment or scientific interpretation changes materially.

Corrections should be traceable through version control rather than silently overwriting provenance.

## 13. Licensing of JLA material

Original JLA documentation, schemas, code-generated descriptions and other original project material may be released under the repository's stated licence. Third-party data retain their original ownership and terms. JLA's licence never overrides a third-party licence.

## 14. Non-endorsement and interpretation notice

Recommended public notice:

> **Jharkhand Life Atlas is an independent, non-partisan research infrastructure. It is not affiliated with or endorsed by the Government of Jharkhand, Government of India, or any source organisation. Government and third-party data remain subject to their respective ownership, licensing and attribution terms. JLA measures data-defined conditions and does not attribute political responsibility.**

## 15. Legal basis references

Policy decisions should be checked against current authoritative sources, including:

- Government Open Data License - India and the Open Government Data Platform India;
- Census of India Terms & Conditions and Copyright/Website Policy;
- Digital Personal Data Protection Act, 2023 and applicable rules/notifications;
- Wild Life (Protection) Act, 1972 as amended;
- any source-specific licence, contract, departmental policy or statutory restriction applicable to a dataset.

This document is a research data-governance policy, not a substitute for case-specific legal advice. High-risk or unclear sources should be withheld pending specialist review.
