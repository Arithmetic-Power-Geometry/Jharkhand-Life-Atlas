# Module 2 — Health & Healthcare Access

Status: **active — authoritative source discovery and rights review**.

This module builds a place-linked evidence layer for healthcare facilities, service capacity, quality certification, service activity and accessibility in Jharkhand. It depends on the completed Core Geography module and keeps historical Census-2011 health amenities separate from current administrative/facility systems unless a verified linkage exists.

## Initial authoritative source inventory

The first discovery pass identified official sources from Census of India, Open Government Data Platform India / Ministry of Health and Family Welfare, Ayushman Bharat Digital Mission / National Health Authority, National Health Systems Resource Centre / National Health Mission, and Central Bureau of Health Intelligence. `sources.yaml` records their intended role and conservative publication status.

The current facility candidates include the OGD All India Health Centres Directory, OGD National Health Portal Hospital Directory, ABDM Health Facility Registry, and existing Census-2011 DCHB village health-amenity fields. District service activity can be sourced separately from the official Jharkhand HMIS OGD catalog. Programme/quality context candidates include Ayushman Arogya Mandir and NQAS official NHSRC pages.

## Hard rules

No source means no published factual value. Missing is not zero. Person-level health records are excluded. District aggregates are never allocated to villages or facilities. Facility coordinates are not guessed. Public and private facility identities remain source-specific until deterministic/evidence-backed matching exists. Historical Census geography and current LGD/facility geography remain distinct unless an official or otherwise defensible crosswalk supports linkage.

## Completion sequence

1. Verify resource-specific licence/terms, update date, export/API availability and granularity for each candidate.
2. Acquire only authoritative reusable data and preserve raw retrieval metadata/checksums where appropriate.
3. Normalize facility types, ownership and health-system fields without erasing source labels.
4. Link facilities to JLA place IDs only through verified codes/coordinates/evidence-backed methods, recording match method and quality.
5. Build observed facility/capacity/service tables; derive accessibility only after facility geography is validated.
6. Add validation, tests, provenance/source registry updates and explicit missingness checks.
7. Integrate Streamlit place/module views, downloads and reports.
8. Require green CI on `main` before changing module status to complete.

No completeness claim is made by this scaffold; it marks the start of Module 2.
