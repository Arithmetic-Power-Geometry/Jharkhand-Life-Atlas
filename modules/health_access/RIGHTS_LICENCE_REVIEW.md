# Module 2 Health — Rights & Licence Review

Reviewed: 2026-09-12
Scope: publication decisions for Health & Healthcare Access evidence admitted or queued by JLA.

## Decision rule

A public catalogue page, API button, metadata record, or licence notice is not by itself permission to publish an unverified payload. JLA separates: (1) source/provider identity, (2) licence/terms, (3) payload acquisition, (4) sensitivity review, (5) attribution, and (6) scientific validation. Publication is allowed only when all applicable gates are satisfied.

## Evidence classes

| Evidence class | Rights basis reviewed | Current JLA decision | Required attribution / constraint |
|---|---|---|---|
| Census 2011 District Census Handbook village amenities used by the validated historical Health extract | Government statistical source used as a source-native derived research extract under JLA's conservative public-data policy | **Admitted only as historical Census-2011 evidence** | Preserve source identity, reference year and Census geography; do not imply current availability or current-LGD equivalence |
| OGD Platform India Health resources, including NIHFW/NHP hospital-directory resources and OGD HMIS/NFHS resources | Government Open Data License - India plus data.gov.in terms reviewed at platform/catalogue level | **Potentially admissible, but each payload remains separately gated** | Acknowledge provider, source, licence and dataset URI/DOI where supplied; do not imply endorsement; capture exact resource identity and snapshot/API provenance |
| ABDM / Health Facility Registry or other sources whose export/republication terms are not established for the intended JLA use | No reusable publication right established in repository evidence | **Excluded from publication** | Do not ingest or republish merely because a page is publicly reachable |
| Person-level, patient-level or otherwise sensitive health records | Outside JLA's publishable Health scope | **Prohibited** | Never expose person-level health data; public-data licensing cannot override privacy/sensitivity restrictions |

## OGD obligations retained by JLA

For an OGD payload to become publishable, JLA must retain provider/source attribution, the Government Open Data License - India notice, and the authoritative dataset/resource URI or DOI when available. JLA must not imply provider endorsement. Personal information, non-shareable/sensitive information and third-party material outside the licence remain excluded.

Rights review does **not** establish that a current resource is scientifically usable. The current NIN/NHP hospital-directory resources remain non-publishable until the exact authoritative machine resource identity and payload are captured, hashes/provenance recorded, observed schema inspected, Jharkhand filtering verified, geographic/temporal semantics validated and the shared source-snapshot gate passes.

## NFHS-5 district factsheet publication boundary

The authoritative OGD catalogue identifies the NFHS-5 India Districts Factsheets resource as Ministry of Health and Family Welfare / IIPS content released through the OGD Platform under the Government Open Data License - India. Repository evidence also records the exact official Catalog API link identity `6f1094bb-24f4-4fe4-8063-cf4cb733279c`.

That catalog/API identity does not authorize publication of an unacquired or unverified workbook. JLA therefore keeps `publication_allowed: false` until the raw workbook bytes are retrieved through an authoritative route, hashed, inspected and validated. The identifier is not treated as a resource UUID or payload identity, and JLA does not construct an endpoint from it.

If the NFHS-5 workbook is acquired, its source annotations and suppression semantics must be preserved. In particular, values withheld because of small unweighted case counts must remain suppressed/null rather than being converted to zero or otherwise imputed without an explicitly validated method. District rows must remain tied to their NFHS-5 reference geography until evidence-backed temporal crosswalks exist.

## Historical Census Health publication boundary

The committed `data/curated/health_access/census_health_access_2011.csv` is admitted only as a validated source-native historical extract. Its publication decision does not authorize any of the following claims:

- current facility inventory;
- current service availability;
- Census-2011 to current-LGD equivalence based on names;
- missing-as-zero interpretation;
- person-level health inference.

Missing source values remain null/blank representations. Current or differently dated Health evidence must pass its own rights, provenance, schema, geography and validation gates.

## Fail-closed outcomes

If provider identity, licence applicability, payload identity, attribution requirements, sensitivity status or republication rights are unresolved, publication permission is `false`. A downstream mirror, cached copy, search result or filename is not sufficient to upgrade that state.

## Authoritative references

- Government Open Data License - India: https://data.gov.in/godl
- OGD Platform India Terms of Use: https://www.data.gov.in/terms-of-use
- Hospital Directory catalogue: https://data.gov.in/catalog/hospital-directory-national-health-portal
- NFHS-5 district factsheet catalogue: https://www.data.gov.in/catalog/national-family-health-survey-5-nfhs-5-india-districts-factsheet-data-provisional
- NFHS-5 official Catalog API link observed on 2026-09-12: https://www.data.gov.in/apis/6f1094bb-24f4-4fe4-8063-cf4cb733279c

This review records the governance decision only. It does not claim acquisition, schema inspection or scientific validity for any payload that has not independently passed those gates.
