# JLA Sustainability Architecture

This document defines the sustainability boundary for the Jharkhand Life Atlas (JLA). It is an operating architecture, not a paywall plan.

## JLA Open

JLA Open is the public evidence layer. Where source rights permit, curated evidence, provenance, methods, validation rules, schemas, research-ready downloads and reproducibility assets remain publicly accessible. Third-party source licences and attribution remain distinct from the licence governing JLA-original software and documentation.

Open publication is fail-closed: no thematic module is presented as complete until its own publication gate verifies authoritative acquisition, rights review, geographic linkage, provenance, schema, indicators, validation, tests, Streamlit presentation, downloads/reports, documentation and green CI on `main`.

## JLA Research

JLA Research is the reusable computation and research-support layer built on the same governed evidence. Planned capabilities may include cross-place comparisons, reproducible research bundles, parameterized reports, bring-your-own-data place linkage, and stable future API contracts. These capabilities must not alter source evidence, hide uncertainty, collapse missing values to zero, or bypass temporal-geography controls.

BYOD workflows must treat uploaded data as separate from JLA public evidence and must not publish person-level or sensitive records. Place linkage must use authoritative identifiers or explicit reviewed crosswalks; fuzzy matching alone is not sufficient for publication-grade integration.

## JLA Studio

JLA Studio is the expertise and commissioned-analysis layer. Appropriate work includes custom GIS/accessibility studies, institutional dashboards, training, commissioned reports, sponsored evidence modules, research collaborations and implementation support.

Commercial value comes from expertise, computation, customization, support and commissioned analysis—not from restricting lawful public evidence or monetizing privacy-invasive data.

## Scientific independence and sponsorship firewall

Sponsors, clients and collaborators may fund questions, infrastructure or analysis, but they may not control findings, suppress inconvenient results, weaken validation, alter missing-data semantics, bypass provenance requirements, or force unsupported geographic harmonization. Sponsored outputs must disclose relevant funding or commissioning relationships and remain subject to the same methodological gates as other JLA work.

## Licensing boundary

JLA must preserve a clear distinction among:

- third-party source data and its original licence/terms;
- JLA-original software;
- JLA-original documentation, schemas, methods and reports; and
- commissioned deliverables whose rights are explicitly agreed without overriding third-party obligations.

No JLA licence statement may imply ownership of third-party evidence beyond the permissions granted by its source.

## Payment infrastructure

No subscription, checkout or payment infrastructure should be added until demonstrated demand exists for a specific paid service. Scientific module completion and public evidence quality take precedence over monetization engineering.

## Implementation principle

Shared infrastructure should be designed once so the same provenance, validation, geography and reporting contracts can support JLA Open, future JLA Research capabilities and JLA Studio engagements without creating separate scientific standards for free and paid users.
