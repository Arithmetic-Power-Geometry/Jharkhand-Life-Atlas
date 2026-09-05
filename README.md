# Jharkhand Life Atlas (JLA) v1.1.0

**Evidence about people, places and access — connected at village level.**

Copyright (C) 2026 Mohammad Amir Khusru Akhtar

JLA is an open, modular, provenance-first public-interest data infrastructure for Jharkhand, India. Original JLA code, documentation, schemas and original data products are licensed under **CC BY 4.0**. Third-party sources retain their own terms; JLA does not relicense them.

## Module 1 status — Core Geography & Census Baseline

The bundled, validated release contains:

- **1** state
- **5** divisions
- **24** districts
- **45** subdivisions
- **264** blocks
- **24** Census 2011 district codes
- **24** official district Primary Census Abstract (PCA) catalog records
- source-reported block-level panchayat and village counts where officially published
- a Jharkhand 2011 state baseline covering population, households, age 0–6, SC/ST, literacy, workers, sex ratio, density, cultivators and agricultural labourers
- an explicit reconciliation dataset preserving disagreements among official administrative snapshots

### Scientific boundary of this release

JLA does **not** claim that a full entity-level panchayat/village master, all village PCA observations, District Census Handbook village amenities, or authoritative map geometry have already been ingested. Their official source families are registered and indexed, but raw records are promoted to curated JLA data only after successful retrieval and validation.

That distinction is deliberate:

> **No source = no published factual value. Missing data is not zero. Catalog discovery is not raw-data ingestion.**

## Run the Streamlit app

### Local

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Streamlit Community Cloud

1. Select repository: `Arithmetic-Power-Geometry/Jharkhand-Life-Atlas`
2. Branch: `main`
3. Main file: `streamlit_app.py`
4. Deploy.

Public mode requires no secrets.

### Enable Admin mode securely

Never commit `.streamlit/secrets.toml` or a real password.

In **Streamlit Community Cloud → App settings → Secrets**, add your own credentials:

```toml
[admin]
username = "admin"
password = "CHANGE-THIS-BEFORE-PUBLIC-SHARING"
```

The Admin page can run integrity checks and generate a ready-to-commit folder for the **next module**. JLA discovers valid `modules/<module_id>/module.yaml` folders automatically.

## Application capabilities

- professional overview with administrative coverage metrics
- Division → District → Subdivision → Block explorer
- source-reported panchayat/village counts with provenance
- official-source conflict/reconciliation audit
- 24-district Census PCA catalog browser
- variable/data dictionary
- filtered CSV downloads
- self-describing research ZIP with sources, dictionary, audit and catalog
- PDF and HTML evidence-profile reports with references
- secure Admin module builder
- dynamic module discovery for future societal modules

Verified map geometry is not bundled in v1.1.0, so the app intentionally does **not** plot approximate or invented locations.

## Repository structure

```text
.github/                 CI and scheduled audit workflows
.streamlit/              Streamlit configuration and secrets example
app_pages/               Streamlit pages
config/                  Project configuration
data/curated/            Curated evidence-backed datasets
docs/                    Data and module policies
jla/                     Reusable Python package
modules/                  Dynamic modules and templates
registry/                Sources, variables and module registry
reports/                 Bibliography and generated-output directory
scripts/                 Integrity commands
tests/                   Automated tests
streamlit_app.py         Streamlit entry point
```

## Evidence and political-neutrality policy

JLA is a non-partisan research infrastructure. It measures publicly observable conditions, accessibility, exposure and service environments. It does not evaluate political parties, elected representatives or governments. Derived indicators describe data-defined conditions and must not be interpreted as attribution of responsibility.

Official sources can disagree because of dates, definitions or administrative change. JLA preserves such disagreements with source IDs, values and reconciliation status instead of silently forcing a single number.

## Core official source families

The Module 1 registry includes Government of Jharkhand state/profile sources, official divisional/block administrative pages, Census of India 2011 Basic Population Figures, Jharkhand PCA district catalogs, District Census Handbooks, and Jharkhand Administrative Atlas catalogs. See `registry/sources.csv` and `modules/core_geography/sources.yaml` for the complete registered list and URLs.

## Validate

```bash
python -m compileall -q jla app_pages modules scripts streamlit_app.py
pytest -q
python scripts/check.py
```

GitHub Actions executes the same checks on pushes and pull requests.

## Citation

Use `CITATION.cff` for JLA and cite the underlying official sources used in an extract. The research bundle carries the source registry so provenance is not separated from the data.
