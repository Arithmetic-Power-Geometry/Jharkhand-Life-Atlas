# JLA Research Bundle Contract

Status: architecture contract only; no paid service or subscription infrastructure is implemented.

JLA Research builds on JLA Open without restricting evidence that can lawfully remain public. It packages reproducible computation, comparisons, place linkage, reporting and research support around openly available evidence.

## Core rules

- JLA Open remains the public evidence layer wherever source licensing permits redistribution.
- Third-party data retain their own source licence, attribution and reuse conditions; the JLA software/content licence does not overwrite them.
- Research bundles may package JLA-original code, schemas, validation outputs, manifests, reports and derived analytical products only when the underlying source rights permit the relevant use.
- Missing values remain missing; they are never converted to zero for convenience.
- Historical and current geographies remain explicitly versioned and require evidence-backed crosswalks.
- Person-level sensitive records are outside JLA Research public/research bundles.
- Sponsors, clients and collaborators cannot control findings, suppress inconvenient results, alter validation thresholds or weaken methodology.

## Planned research capabilities

1. Cross-module and cross-period comparison specifications with explicit geography and denominator compatibility checks.
2. Reproducible research bundles containing machine-readable manifests, source/provenance records, code, environment metadata, validation summaries, tables/figures inputs and report outputs.
3. BYOD place linkage that accepts institution-provided aggregate/non-sensitive data and links only through authoritative identifiers or auditable crosswalks; fuzzy joins are not a default publication mechanism.
4. Reproducible report generation from verified module outputs.
5. Future API contracts for read-only access to publishable module evidence, provenance, status and validation metadata.

## Bundle minimum manifest

Every future research bundle should record:

- bundle identifier and version;
- generation timestamp and code commit;
- included modules and module status at generation time;
- source identifiers, retrieval metadata and applicable source licences;
- geography version(s) and crosswalk version(s);
- observation/reporting periods;
- transformations and indicator definitions;
- validation/test results;
- known limitations and unresolved gaps;
- files with cryptographic hashes;
- citation guidance and JLA-original licence scope.

## Publication boundary

A research bundle must not turn an IN DEVELOPMENT or PLANNED module into apparently published evidence. Unverified modules may contribute architecture, source inventories, schemas or methods documentation only when clearly labelled as such.

## Sustainability boundary

JLA may charge for expertise, computation, custom analysis, support, training and commissioned work while preserving open evidence where licensing permits. Payment/subscription infrastructure remains deferred until demonstrated demand justifies implementation.
